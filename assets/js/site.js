/* Small progressive enhancements. Content and navigation work without this file.
   CSS, JavaScript and authored Markdown stay separate to make editing easier. */
(() => {
  'use strict';
  const root = document.documentElement;
  const menu = document.querySelector('.nav-toggle');
  const navigation = document.querySelector('#site-navigation');
  const theme = document.querySelector('#theme-select');
  const themes = ['halo', 'resident', 'balanced', 'terminal', 'sunset', 'paper'];
  const mobile = window.matchMedia('(max-width: 620px)');

  function closeMenu(restoreFocus = false) {
    navigation?.classList.remove('is-open');
    menu?.setAttribute('aria-expanded', 'false');
    if (restoreFocus) menu?.focus();
  }
  if (menu && navigation) {
    menu.addEventListener('click', () => {
      const expanded = menu.getAttribute('aria-expanded') !== 'true';
      menu.setAttribute('aria-expanded', String(expanded));
      navigation.classList.toggle('is-open', expanded);
    });
    navigation.addEventListener('click', event => {
      if (event.target.closest('a')) closeMenu();
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') closeMenu(true);
    });
    document.addEventListener('click', event => {
      if (!navigation.contains(event.target) && !menu.contains(event.target)) closeMenu();
    });
    mobile.addEventListener('change', () => closeMenu());
  }
  if (theme) {
    theme.value = themes.includes(root.dataset.theme) ? root.dataset.theme : 'halo';
    theme.addEventListener('change', () => {
      if (!themes.includes(theme.value)) return;
      root.dataset.theme = theme.value;
      try { localStorage.setItem('kaz-interface-theme', theme.value); } catch { /* Session theme still works. */ }
    });
    window.addEventListener('storage', event => {
      if (event.key === 'kaz-interface-theme' && themes.includes(event.newValue)) {
        root.dataset.theme = event.newValue;
        theme.value = event.newValue;
      }
    });
  }

  // Read each card once. Filtering touches only hidden state; sorting moves the
  // existing nodes so image state and article markup are preserved.
  document.querySelectorAll('[data-filter-board]').forEach(board => {
    const list = board.querySelector('[data-filter-list]');
    if (!list) return;
    const rows = Array.from(list.querySelectorAll('[data-filter-item]'));
    const records = rows.map((node, index) => ({node, index,
      text: node.textContent.toLocaleLowerCase('en-GB'),
      title: node.dataset.title || '', date: node.dataset.date || '',
      score: Number(node.dataset.score || 0), category: node.dataset.category || ''}));
    const query = board.querySelector('[data-filter-query]');
    const category = board.querySelector('[data-filter-category]');
    const sort = board.querySelector('[data-filter-sort]');
    const count = board.querySelector('[data-filter-count]');
    const empty = board.querySelector('[data-filter-empty]');
    let timer;
    function apply() {
      const words = (query?.value || '').trim().toLocaleLowerCase('en-GB').split(/\s+/).filter(Boolean);
      let visible = 0;
      for (const row of records) {
        const match = words.every(word => row.text.includes(word)) &&
          (!category || category.value === 'all' || row.category === category.value);
        row.node.hidden = !match;
        if (match) visible++;
      }
      if (count) count.textContent = `${visible} of ${rows.length} entries`;
      if (empty) empty.hidden = visible !== 0;
    }
    query?.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(apply, 120); });
    category?.addEventListener('change', apply);
    sort?.addEventListener('change', () => {
      const sorted = [...records].sort((a, b) => {
        if (sort.value === 'title') return a.title.localeCompare(b.title, 'en-GB');
        if (sort.value === 'score') return b.score - a.score || a.index - b.index;
        return (sort.value === 'oldest' ? a.date.localeCompare(b.date) : b.date.localeCompare(a.date)) || a.index - b.index;
      });
      const fragment = document.createDocumentFragment();
      sorted.forEach(row => fragment.append(row.node));
      list.append(fragment);
      apply();
    });
    apply();
  });

  async function copy(text, button, status) {
    const initial = button.textContent;
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(text);
      button.textContent = 'Copied';
      if (status) status.textContent = 'Copied to clipboard.';
    } catch {
      button.textContent = 'Select and copy manually';
      if (status) status.textContent = 'Clipboard unavailable. Use the address bar or select the code.';
    }
    setTimeout(() => { button.textContent = initial; }, 2500);
  }
  document.querySelector('[data-copy-link]')?.addEventListener('click', event => {
    const url = new URL(window.location.href);
    url.hash = 'post-body';
    copy(url.href, event.currentTarget, document.querySelector('[data-copy-status]'));
  });
  document.querySelectorAll('.prose pre').forEach(pre => {
    pre.tabIndex = 0;
    pre.setAttribute('aria-label', 'Code example; scroll horizontally if needed');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'code-copy';
    button.textContent = 'Copy code';
    button.addEventListener('click', () => copy(pre.textContent, button));
    pre.before(button);
  });
  // Hide compact navigation only after its handlers are ready.
  document.querySelectorAll('.enhancement').forEach(node => { node.hidden = false; });
  root.classList.add('js');
})();
