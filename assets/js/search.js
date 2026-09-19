/* Search stays local, readable and resilient when the network is unavailable. */
(() => {
  'use strict';
  const form=document.querySelector('#search-form'), input=document.querySelector('#search-query');
  const status=document.querySelector('#search-status'), output=document.querySelector('#search-results');
  if(!form||!input||!status||!output)return;
  let dataPromise, sequence=0;
  const cacheKey='kaz-search-index-v1';
  const normalise=value=>String(value??'').toLocaleLowerCase('en-GB').normalize('NFKD').replace(/[\u0300-\u036f]/g,'');
  const termsFor=query=>normalise(query).split(/\s+/).filter(Boolean).slice(0,12);
  const cacheIndex=pages=>{try{localStorage.setItem(cacheKey,JSON.stringify(pages));}catch{}};
  const cachedIndex=()=>{try{return JSON.parse(localStorage.getItem(cacheKey)||'null');}catch{return null;}};
  async function loadIndex(){
    dataPromise ||= fetch('/search-index.json',{credentials:'same-origin'}).then(response=>{if(!response.ok)throw new Error('Index unavailable');return response.json();})
      .then(pages=>{cacheIndex(pages);return pages;}).catch(error=>{dataPromise=undefined;const cached=cachedIndex();if(cached)return cached;throw error;});
    return dataPromise;
  }
  function score(page,terms){
    const title=normalise(page.title), section=normalise(page.section), tags=normalise((page.tags||[]).join(' '));
    const body=normalise(String(page.description||'')+' '+String(page.text||'')); let total=0;
    for(const term of terms){if(title.includes(term))total+=12;else if(tags.includes(term))total+=8;else if(section.includes(term))total+=5;else if(body.includes(term))total+=1;else return 0;}
    return total;
  }
  function highlight(text,terms){
    const fragment=document.createDocumentFragment();
    const escaped=terms.map(term=>term.replace(/[.*+?^$()|[\]\\]/g,'\\$&')).join('|');
    if(!escaped){fragment.append(document.createTextNode(String(text??'')));return fragment;}
    const parts=String(text??'').split(new RegExp('('+escaped+')','ig'));
    parts.forEach(part=>{if(terms.some(term=>normalise(part)===term)){const mark=document.createElement('mark');mark.textContent=part;fragment.append(mark);}else fragment.append(document.createTextNode(part));});
    return fragment;
  }
  async function run(updateUrl=true){
    const current=++sequence, query=input.value.trim().slice(0,200);
    output.replaceChildren();output.setAttribute('aria-busy','false');
    if(!query){status.textContent='Enter a few words to find a page.';return;}
    if(updateUrl){const url=new URL(window.location.href);url.searchParams.set('q',query);history.replaceState(null,'',url);}
    status.textContent='Searching…';output.setAttribute('aria-busy','true');
    try{
      const pages=await loadIndex();if(current!==sequence)return;
      const terms=termsFor(query);
      const results=pages.map(page=>({page,score:score(page,terms)})).filter(item=>item.score>0)
        .sort((a,b)=>b.score-a.score||(b.page.date||'').localeCompare(a.page.date||'')||a.page.title.localeCompare(b.page.title));
      const fragment=document.createDocumentFragment();
      results.forEach(({page})=>{
        const target=new URL(page.url,location.origin);if(target.origin!==location.origin)return;
        const article=document.createElement('article');article.className='search-result';
        const heading=document.createElement('h2'),link=document.createElement('a');link.href=target.pathname;link.append(highlight(page.title,terms));heading.append(link);
        const meta=document.createElement('small');meta.className='search-meta';meta.textContent=[page.section,page.entryType?.replaceAll('-',' '),page.date,page.minutes?(page.minutes+' min read'):''].filter(Boolean).join(' · ');
        const description=document.createElement('p');description.append(highlight(page.description,terms));article.append(heading,meta,description);fragment.append(article);
      });
      output.append(fragment);output.setAttribute('aria-busy','false');status.textContent=results.length+' matching '+(results.length===1?'page':'pages')+'.';
      if(!results.length)status.textContent+=' Try fewer words, a language name, or the site map.';
    }catch{output.setAttribute('aria-busy','false');if(current===sequence)status.textContent='Search could not load. Submit again to retry, or browse the site map below.';}
  }
  form.addEventListener('submit',event=>{event.preventDefault();run();});
  document.querySelector('[data-search-clear]')?.addEventListener('click',()=>{sequence++;input.value='';output.replaceChildren();output.setAttribute('aria-busy','false');status.textContent='Enter a few words to find a page.';const url=new URL(window.location.href);url.searchParams.delete('q');history.replaceState(null,'',url);input.focus();});
  input.value=new URLSearchParams(location.search).get('q')?.slice(0,200)||'';
  if(input.value.trim())run(false);
})();