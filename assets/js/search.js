/* Local search: weighted fields, prefix matching and conservative typo tolerance. */
(() => {
  'use strict';
  const form=document.querySelector('#search-form'), input=document.querySelector('#search-query');
  const status=document.querySelector('#search-status'), output=document.querySelector('#search-results');
  if(!form||!input||!status||!output)return;

  let dataPromise, sequence=0, typingTimer;
  const cacheKey='kaz-search-index-v2';
  const normalise=value=>String(value??'').toLocaleLowerCase('en-GB').normalize('NFKD').replace(/[\u0300-\u036f]/g,'');
  const tokenise=value=>normalise(value).match(/[a-z0-9+#.-]+/g)||[];

  function queryParts(query){
    const source=normalise(query).trim();
    const phrases=[];
    const unquoted=source.replace(/"([^"]{2,80})"/g,(_,phrase)=>{phrases.push(phrase.trim());return ' ';});
    const terms=[...new Set([...phrases.flatMap(tokenise),...tokenise(unquoted)])].slice(0,12);
    return {terms,phrases:phrases.slice(0,4)};
  }

  function withinOneEdit(left,right){
    if(left===right)return true;
    if(Math.abs(left.length-right.length)>1)return false;
    let i=0,j=0,edits=0;
    while(i<left.length&&j<right.length){
      if(left[i]===right[j]){i++;j++;continue;}
      if(++edits>1)return false;
      if(left.length>right.length)i++;
      else if(right.length>left.length)j++;
      else{i++;j++;}
    }
    if(i<left.length||j<right.length)edits++;
    return edits<=1;
  }

  function fieldScore(term,text,tokens,weights,fuzzy=false){
    if(tokens.includes(term))return weights.exact;
    if(term.length>=2&&tokens.some(word=>word.startsWith(term)))return weights.prefix;
    if(text.includes(term))return weights.contains;
    if(fuzzy&&term.length>=5&&tokens.some(word=>word.length>=4&&withinOneEdit(term,word)))return weights.fuzzy;
    return 0;
  }

  function score(page,parts){
    const fields={
      title:normalise(page.title),
      tags:normalise((page.tags||[]).join(' ')),
      section:normalise(page.section),
      description:normalise(page.description),
      body:normalise(page.text)
    };
    const tokens=Object.fromEntries(Object.entries(fields).map(([key,value])=>[key,tokenise(value)]));
    let total=0;

    for(const phrase of parts.phrases){
      if(fields.title.includes(phrase))total+=36;
      else if(fields.description.includes(phrase))total+=16;
      else if(fields.body.includes(phrase))total+=5;
      else return 0;
    }

    for(const term of parts.terms){
      const best=Math.max(
        fieldScore(term,fields.title,tokens.title,{exact:18,prefix:14,contains:10,fuzzy:5},true),
        fieldScore(term,fields.tags,tokens.tags,{exact:14,prefix:11,contains:8,fuzzy:4},true),
        fieldScore(term,fields.section,tokens.section,{exact:8,prefix:7,contains:5,fuzzy:0}),
        fieldScore(term,fields.description,tokens.description,{exact:6,prefix:5,contains:3,fuzzy:0}),
        fieldScore(term,fields.body,tokens.body,{exact:3,prefix:2,contains:1,fuzzy:0})
      );
      if(!best)return 0;
      total+=best;
    }

    if(parts.terms.length&&parts.terms.every(term=>tokens.title.includes(term)))total+=8;
    return total;
  }

  function highlight(text,terms){
    const fragment=document.createDocumentFragment();
    const escaped=terms.filter(Boolean).map(term=>term.replace(/[.*+?^$()|[\]\\]/g,'\\$&')).join('|');
    if(!escaped){fragment.append(document.createTextNode(String(text??'')));return fragment;}
    const parts=String(text??'').split(new RegExp('('+escaped+')','ig'));
    parts.forEach(part=>{
      if(terms.some(term=>normalise(part)===term)){
        const mark=document.createElement('mark');mark.textContent=part;fragment.append(mark);
      }else fragment.append(document.createTextNode(part));
    });
    return fragment;
  }

  const cacheIndex=pages=>{try{localStorage.setItem(cacheKey,JSON.stringify({version:2,savedAt:Date.now(),pages}));}catch{}};
  const cachedIndex=()=>{try{const cached=JSON.parse(localStorage.getItem(cacheKey)||'null');return cached?.version===2&&Array.isArray(cached.pages)?cached.pages:null;}catch{return null;}};

  async function loadIndex(){
    dataPromise ||= fetch('/search-index.json',{credentials:'same-origin'})
      .then(response=>{if(!response.ok)throw new Error('Index unavailable');return response.json();})
      .then(pages=>{if(!Array.isArray(pages))throw new Error('Invalid index');cacheIndex(pages);return pages;})
      .catch(error=>{dataPromise=undefined;const cached=cachedIndex();if(cached)return cached;throw error;});
    return dataPromise;
  }

  function clearResults(updateUrl=true,focus=false){
    sequence++;clearTimeout(typingTimer);output.replaceChildren();output.setAttribute('aria-busy','false');
    status.textContent='Enter a few words to find a page.';
    if(updateUrl){const url=new URL(window.location.href);url.searchParams.delete('q');history.replaceState(null,'',url);}
    if(focus)input.focus();
  }

  async function run(updateUrl=true){
    clearTimeout(typingTimer);
    const current=++sequence, query=input.value.trim().slice(0,200);
    output.replaceChildren();output.setAttribute('aria-busy','false');
    if(!query){clearResults(updateUrl);return;}
    if(updateUrl){const url=new URL(window.location.href);url.searchParams.set('q',query);history.replaceState(null,'',url);}
    status.textContent='Searching…';output.setAttribute('aria-busy','true');

    try{
      const pages=await loadIndex();if(current!==sequence)return;
      const parts=queryParts(query);
      if(!parts.terms.length){status.textContent='Enter a word, title or tag to search.';output.setAttribute('aria-busy','false');return;}
      const results=pages.map(page=>({page,score:score(page,parts)})).filter(item=>item.score>0)
        .sort((a,b)=>b.score-a.score||(b.page.date||'').localeCompare(a.page.date||'')||a.page.title.localeCompare(b.page.title));

      const fragment=document.createDocumentFragment();
      results.forEach(({page})=>{
        const target=new URL(page.url,location.origin);if(target.origin!==location.origin)return;
        const article=document.createElement('article');article.className='search-result';
        const heading=document.createElement('h2'),link=document.createElement('a');link.href=target.pathname;link.append(highlight(page.title,parts.terms));heading.append(link);
        const meta=document.createElement('small');meta.className='search-meta';meta.textContent=[page.section,page.entryType?.replaceAll('-',' '),page.date,page.minutes?(page.minutes+' min read'):''].filter(Boolean).join(' · ');
        const description=document.createElement('p');description.append(highlight(page.description,parts.terms));
        article.append(heading,meta,description);fragment.append(article);
      });
      output.append(fragment);output.setAttribute('aria-busy','false');
      status.textContent=results.length+' matching '+(results.length===1?'page':'pages')+'.';
      if(!results.length)status.textContent+=' Try fewer words, a shorter prefix, or the site map.';
    }catch{
      output.setAttribute('aria-busy','false');
      if(current===sequence)status.textContent='Search could not load. Submit again to retry, or browse the site map below.';
    }
  }

  form.addEventListener('submit',event=>{event.preventDefault();run();});
  input.addEventListener('input',()=>{
    clearTimeout(typingTimer);
    const query=input.value.trim();
    if(!query){clearResults();return;}
    if(query.length<2)return;
    typingTimer=setTimeout(()=>run(),220);
  });
  document.querySelector('[data-search-clear]')?.addEventListener('click',()=>{input.value='';clearResults(true,true);});
  input.value=new URLSearchParams(location.search).get('q')?.slice(0,200)||'';
  if(input.value.trim())run(false);
})();
