/* Runs before first paint. Storage can be blocked, so a preference must never
   prevent a page from loading. Themes only change the root attribute. */
(() => {
  'use strict';
  const themes = ['halo', 'resident', 'balanced', 'terminal', 'sunset', 'paper'];
  try {
    const saved = localStorage.getItem('kaz-interface-theme');
    if (themes.includes(saved)) document.documentElement.dataset.theme = saved;
  } catch { /* Keep the readable default when storage is unavailable. */ }
})();
