(() => {
  'use strict';
  if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    navigator.serviceWorker.register('/sw.js').catch(() => { /* Online reading does not depend on offline caching. */ });
  }
  const theme = document.querySelector('#theme');
  if (theme) {
    theme.value = document.documentElement.dataset.theme;
    theme.addEventListener('change', () => {
      document.documentElement.dataset.theme = theme.value;
      try { localStorage.setItem('kaz-theme-v6', theme.value); } catch { /* Preference remains valid for this page. */ }
    });
  }
  document.addEventListener('keydown', event => {
    const menu = document.querySelector('.mobile-nav[open]');
    if (event.key === 'Escape' && menu) {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });
  const filter = document.querySelector('[data-filter]');
  const normalize = value => String(value).normalize('NFKC').toLocaleLowerCase().trim().replace(/\s+/g, ' ');
  if (filter) {
    const entries = [...document.querySelectorAll('[data-record]')];
    const status = document.querySelector('[data-filter-status]');
    const empty = document.querySelector('[data-filter-empty]');
    const apply = () => {
      const terms = normalize(filter.value).split(' ');
      let count = 0;
      for (const entry of entries) {
        entry.hidden = !terms.every(term => normalize(entry.textContent).includes(term));
        if (!entry.hidden) count++;
      }
      status.textContent = `${count} of ${entries.length} entries shown`;
      empty.hidden = count !== 0;
    };
    filter.addEventListener('input', apply);
    apply();
  }
  const form = document.querySelector('#search-form');
  if (!form) return;
  const query = document.querySelector('#query');
  const status = document.querySelector('#search-status');
  const results = document.querySelector('#search-results');
  const retry = document.querySelector('#search-retry');
  let index;
  let pending;
  let serial = 0;
  const load = async () => {
    if (index) return index;
    if (!pending) {
      pending = fetch('/search-index.json').then(response => {
        if (!response.ok) throw new Error('Search unavailable');
        return response.json();
      }).then(data => {
        if (!Array.isArray(data)) throw new Error('Invalid index');
        index = data.filter(item => typeof item.title === 'string' && typeof item.text === 'string' && typeof item.url === 'string' && /^\/(?!\/)/.test(item.url) && !/[\\\u0000-\u001f]/.test(item.url));
        return index;
      }).finally(() => { pending = null; });
    }
    return pending;
  };
  const search = async () => {
    const request = ++serial;
    const value = normalize(query.value);
    results.replaceChildren();
    retry.hidden = true;
    const url = new URL(location.href);
    if (value) url.searchParams.set('q', query.value); else url.searchParams.delete('q');
    history.replaceState(null, '', url);
    if (!value) { status.textContent = 'Enter a word or topic to search.'; return; }
    status.textContent = 'Loading the notebook index…';
    try {
      const data = await load();
      if (request !== serial) return;
      const terms = value.split(' ');
      const found = data.filter(item => terms.every(term => normalize([item.title, item.summary, item.text, ...(Array.isArray(item.tags) ? item.tags : [])].join(' ')).includes(term)));
      found.sort((a, b) => Number(normalize(b.title).includes(value)) - Number(normalize(a.title).includes(value)) || a.title.localeCompare(b.title));
      status.textContent = found.length ? `${found.length} ${found.length === 1 ? 'page' : 'pages'} found` : 'No pages match. Try a shorter term or browse the site directory.';
      for (const item of found) {
        const row = document.createElement('li');
        const heading = document.createElement('h2');
        const anchor = document.createElement('a');
        anchor.href = item.url;
        anchor.textContent = item.title;
        heading.append(anchor);
        const excerpt = document.createElement('p');
        excerpt.textContent = typeof item.summary === 'string' && item.summary ? item.summary : item.text.slice(0, 180);
        row.append(heading, excerpt);
        results.append(row);
      }
    } catch {
      if (request !== serial) return;
      status.textContent = 'Search could not load. Retry, or use the site directory in the footer.';
      retry.hidden = false;
    }
  };
  form.addEventListener('submit', event => { event.preventDefault(); search(); });
  form.addEventListener('reset', () => { query.value = ''; search(); query.focus(); });
  retry.addEventListener('click', search);
  query.value = new URLSearchParams(location.search).get('q') || '';
  if (query.value) search();
})();
