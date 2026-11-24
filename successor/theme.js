(() => {
  try {
    const legacy = localStorage.getItem('kaz-interface-theme');
    const theme = localStorage.getItem('kaz-theme-v6') || (legacy === 'halo' ? 'forerunner' : legacy);
    if (['balanced', 'forerunner', 'resident'].includes(theme)) document.documentElement.dataset.theme = theme;
  } catch { /* Reading and the default theme remain available without storage. */ }
})();
