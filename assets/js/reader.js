/* Deep reading enhancements remain optional and never replace article content. */
(() => {
  'use strict';
  const root = document.documentElement;
  const article = document.querySelector('[data-article-body]');
  const status = document.querySelector('[data-reader-status]');
  const scaleKey = 'kaz-reading-scale';
  const tocKey = 'kaz-toc-open';
  const clamp = value => Math.min(1.2, Math.max(.9, Math.round(value * 20) / 20));
  const announce = message => { if (status) status.textContent = message; };
  if (article) {
    let scale = 1;
    try { scale = clamp(Number(localStorage.getItem(scaleKey)) || 1); } catch {}
    const applyScale = () => {
      root.style.setProperty('--reading-scale', scale);
      const value = document.querySelector('[data-font-value]');
      if (value) value.textContent = Math.round(scale * 100) + '%';
    };
    applyScale();
    document.querySelector('[data-font-decrease]')?.addEventListener('click', () => {
      scale = clamp(scale - .05); applyScale(); announce('Reading size ' + Math.round(scale * 100) + ' percent.');
      try { localStorage.setItem(scaleKey, String(scale)); } catch {}
    });
    document.querySelector('[data-font-increase]')?.addEventListener('click', () => {
      scale = clamp(scale + .05); applyScale(); announce('Reading size ' + Math.round(scale * 100) + ' percent.');
      try { localStorage.setItem(scaleKey, String(scale)); } catch {}
    });
    document.querySelector('[data-font-reset]')?.addEventListener('click', () => {
      scale = 1; applyScale(); announce('Reading size reset to 100 percent.');
      try { localStorage.removeItem(scaleKey); } catch {}
    });
  }
  const contents = document.querySelector('.post-contents');
  if (contents) {
    try { contents.open = localStorage.getItem(tocKey) === 'true'; } catch {}
    contents.addEventListener('toggle', () => { try { localStorage.setItem(tocKey, String(contents.open)); } catch {} });
  }
  document.querySelector('[data-print-post]')?.addEventListener('click', () => window.print());
  document.querySelector('[data-share-post]')?.addEventListener('click', async event => {
    const button = event.currentTarget;
    const original = button.textContent;
    const share = {title: document.title, url: window.location.href};
    try {
      if (navigator.share) await navigator.share(share);
      else if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(share.url);
      else throw new Error('Share unavailable');
      button.textContent = navigator.share ? 'Shared' : 'Link copied';
      announce(navigator.share ? 'Share sheet opened.' : 'Post link copied.');
    } catch (error) {
      if (error?.name !== 'AbortError') announce('Sharing is unavailable; use the permalink above.');
    }
    setTimeout(() => { button.textContent = original; }, 2200);
  });
})();