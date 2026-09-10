/* Search is fetched only on the search route, then cached for this page visit. */
(() => {
  'use strict';
  const form = document.querySelector('#search-form');
  const input = document.querySelector('#search-query');
  const status = document.querySelector('#search-status');
  const output = document.querySelector('#search-results');
  if (!form || !input || !status || !output) return;
  let dataPromise;
  let sequence = 0;
  async function run(updateUrl = true) {
    const current = ++sequence;
    const query = input.value.trim().slice(0, 200);
    output.replaceChildren();
    if (!query) { status.textContent = 'Enter a few words to find a page.'; return; }
    if (updateUrl) {
      const url = new URL(window.location.href);
      url.searchParams.set('q', query);
      history.replaceState(null, '', url);
    }
    status.textContent = 'Searching…';
    try {
      dataPromise ||= fetch('/search-index.json', {credentials: 'same-origin'}).then(response => {
        if (!response.ok) throw new Error('Index unavailable');
        return response.json();
      }).catch(error => { dataPromise = undefined; throw error; });
      const pages = await dataPromise;
      if (current !== sequence) return;
      const terms = query.toLocaleLowerCase('en-GB').split(/\s+/);
      const results = pages.map(page => {
        const title = page.title.toLocaleLowerCase('en-GB');
        const haystack = `${title} ${page.description} ${page.text}`.toLocaleLowerCase('en-GB');
        return {page, score: terms.every(term => haystack.includes(term)) ?
          1 + terms.filter(term => title.includes(term)).length * 5 : 0};
      }).filter(item => item.score > 0).sort((a,b) => b.score-a.score || a.page.title.localeCompare(b.page.title));
      status.textContent = `${results.length} matching ${results.length === 1 ? 'page' : 'pages'}.`;
      const fragment = document.createDocumentFragment();
      results.forEach(({page}) => {
        const target = new URL(page.url, location.origin);
        if (target.origin !== location.origin) return;
        const article = document.createElement('article');
        article.className = 'search-result';
        const heading = document.createElement('h2');
        const link = document.createElement('a');
        link.href = target.pathname;
        link.textContent = page.title;
        heading.append(link);
        const description = document.createElement('p');
        description.textContent = page.description;
        article.append(heading, description);
        fragment.append(article);
      });
      output.append(fragment);
      if (!results.length) status.textContent += ' Try fewer words, a language name, or the site map.';
    } catch {
      if (current === sequence) status.textContent = 'Search could not load. Submit again to retry, or browse the site map below.';
    }
  }
  form.addEventListener('submit', event => { event.preventDefault(); run(); });
  input.value = new URLSearchParams(location.search).get('q')?.slice(0,200) || '';
  if (input.value.trim()) run(false);
})();
