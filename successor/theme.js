(() => {
  try {
    const theme = localStorage.getItem('kaz-theme-v6');
    if (['balanced', 'forerunner', 'resident'].includes(theme)) document.documentElement.dataset.theme = theme;
  } catch { /* Reading and the default theme remain available without storage. */ }
})();
