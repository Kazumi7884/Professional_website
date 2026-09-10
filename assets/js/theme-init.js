/* Apply a stored preference before first paint, including V5.1 migration. */
(() => {
  'use strict';
  const themes = ['halo', 'resident', 'balanced'];
  const legacy = { paper: 'balanced', terminal: 'resident', sunset: 'balanced' };
  try {
    const saved = localStorage.getItem('kaz-interface-theme');
    const theme = legacy[saved] || saved;
    if (themes.includes(theme)) document.documentElement.dataset.theme = theme;
  } catch { /* The default remains readable with storage blocked. */ }
})();
