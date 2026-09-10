/* Native controls keep writing usable in Firefox/Zen without a framework.
   Recovery copies are local to this browser; Save writes the actual Markdown. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const token = document.querySelector('meta[name="studio-token"]').content;
  const recoveryKey = 'kaz-writing-recovery-v1';
  let posts = [], current = null, dirty = false, manualSlug = false, busy = false;
  let previewTimer, previewSequence = 0;
  const fields = ['post-title', 'post-summary', 'post-section', 'post-slug', 'post-date', 'post-kind', 'post-tags', 'post-body', 'post-draft'];
  const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
  const slug = value => value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function status(message, error = false) { $('save-status').textContent = message; $('save-status').dataset.error = String(error); }
  async function api(route, payload) {
    const response = await fetch(`/__studio/api/${route}`, {
      method: payload === undefined ? 'GET' : 'POST',
      headers: {'X-Studio-Token': token, 'Content-Type': 'application/json'},
      ...(payload === undefined ? {} : {body: JSON.stringify(payload)})
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'The request failed. Your text is still in the editor.');
    return result;
  }
  function payload() {
    const section = $('post-section').value;
    return {path: current?.path || `${section ? section+'/' : ''}${$('post-slug').value}.md`,
      revision: current?.revision || null,
      metadata: {...(current?.metadata || {}), title: $('post-title').value, description: $('post-summary').value,
        date: $('post-date').value, entryType: $('post-kind').value, draft: $('post-draft').value === 'draft',
        tags: [...new Set($('post-tags').value.split(',').map(t => t.trim()).filter(Boolean))]},
      body: $('post-body').value};
  }
  function remember() {
    try {
      localStorage.setItem(recoveryKey, JSON.stringify({document: payload(), values: Object.fromEntries(fields.map(id => [id, $(id).value]))}));
      status('Unsaved changes · recovery copy kept in this browser');
    } catch { status('Unsaved changes · browser recovery unavailable. Save or download your post.', true); }
  }
  function clearRecovery() { try { localStorage.removeItem(recoveryKey); } catch { /* File saving is independent. */ } $('recovery').hidden = true; }
  function count() {
    const words = $('post-body').value.trim().split(/\s+/).filter(Boolean).length;
    $('word-count').textContent = `${words} words · ${Math.max(1, Math.ceil(words / 200))} min read`;
    $('save-post').textContent = $('post-draft').value === 'draft' ? 'Save draft' : 'Save ready post';
  }
  function changed() {
    dirty = true; count(); remember();
    clearTimeout(previewTimer);
    if (document.querySelector('.compose-surface').dataset.view !== 'write') previewTimer = setTimeout(preview, 350);
  }
  function mayLeave() { return !busy && (!dirty || window.confirm('Leave this post without saving? Download or save first to keep your changes.')); }
  function ensureSection(section) {
    if (![...$('post-section').options].some(option => option.value === section)) {
      $('post-section').add(new Option(section || 'Top-level pages', section));
    }
  }
  function fill(document) {
    current = document;
    const meta = document?.metadata || {};
    const section = document ? document.path.split('/').slice(0, -1).join('/') : 'blog';
    ensureSection(section);
    $('post-section').value = section;
    $('post-section').disabled = Boolean(document?.revision);
    $('post-slug').value = document ? document.path.split('/').pop().replace(/\.md$/, '') : '';
    $('post-slug').readOnly = Boolean(document?.revision);
    $('post-title').value = meta.title || '';
    $('post-summary').value = meta.description || '';
    $('post-date').value = String(meta.date || today()).slice(0, 10);
    const kind = meta.entryType || 'page';
    if (![...$('post-kind').options].some(option => option.value === kind)) $('post-kind').add(new Option(kind, kind));
    $('post-kind').value = kind;
    if (!document) $('post-kind').value = 'post';
    $('post-tags').value = (meta.tags || []).join(', ');
    $('post-body').value = document?.body || '';
    $('post-draft').value = document && meta.draft !== true ? 'ready' : 'draft';
    $('document-label').textContent = document ? `content/${document.path}` : 'New post';
    $('editor-heading').textContent = document ? 'Make it your own.' : 'Put it into words.';
    dirty = false; manualSlug = Boolean(document); count(); renderList();
    status(document ? 'Opened from your website folder' : 'Not yet saved');
    if (document.querySelector('.compose-surface').dataset.view !== 'write') preview();
  }
  function renderList() {
    const words = $('post-search').value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const state = $('post-state').value;
    const matches = posts.filter(p => words.every(word => `${p.title} ${p.path}`.toLowerCase().includes(word)) &&
      (state === 'all' || (state === 'draft' ? p.draft : p.kind === 'post')));
    $('post-list').replaceChildren();
    $('library-count').textContent = `${matches.length} of ${posts.length} pages`;
    for (const post of matches) {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'document-button';
      button.textContent = post.title;
      if (current?.path === post.path) button.setAttribute('aria-current', 'page');
      const detail = document.createElement('small'); detail.textContent = `${post.error ? 'Needs metadata repair' : post.draft ? 'Draft' : 'In site'} · ${post.path}`;
      button.append(detail);
      button.addEventListener('click', async () => {
        if (!mayLeave()) return;
        busy = true;
        try { const document = await api(`post?path=${encodeURIComponent(post.path)}`); clearRecovery(); fill(document); }
        catch (error) { status(error.message, true); }
        finally { busy = false; }
      });
      $('post-list').append(button);
    }
    if (!matches.length) $('post-list').textContent = 'No pages match. Try another title or clear the filters.';
  }
  async function refreshList() {
    const result = await api('posts'); posts = result.posts;
    const tracks = new Set(posts.map(p => p.path.split('/').slice(0, -1).join('/')));
    for (const path of tracks) {
      if (/^learning\/[^/]+$/.test(path)) ensureSection(`${path}/posts`);
      ensureSection(path);
    }
    renderList();
  }
  async function preview() {
    const sequence = ++previewSequence;
    const draft = payload();
    try {
      const result = await api('preview', {body: draft.body});
      if (sequence !== previewSequence) return;
      const theme = $('desk-theme').value;
      const safeBody = DOMPurify.sanitize(result.html, {USE_PROFILES: {html: true}, FORBID_TAGS: ['style', 'form', 'input', 'button', 'iframe'], FORBID_ATTR: ['style']});
      $('post-preview').srcdoc = `<!DOCTYPE html><html lang="en-GB" data-theme="${theme}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="/__studio/site.css"><link rel="stylesheet" href="/__studio/studio.css"></head><body class="preview-document"><article class="prose"><p class="eyebrow">${draft.metadata.draft ? 'Draft preview' : 'Post preview'}</p><h1>${escape(draft.metadata.title || 'Untitled post')}</h1><p>${escape(draft.metadata.description || '')}</p><hr>${safeBody}</article></body></html>`;
    } catch (error) { status(`Preview failed: ${error.message}`, true); }
  }
  function view(mode) {
    document.querySelector('.compose-surface').dataset.view = mode;
    $('post-body').hidden = mode === 'preview';
    $('post-preview').hidden = mode === 'write';
    document.querySelector('.format-toolbar').hidden = mode === 'preview';
    for (const name of ['write', 'preview', 'split']) $(`${name}-view`).setAttribute('aria-pressed', String(name === mode));
    if (mode !== 'write') preview();
  }
  const formats = {
    heading: ['\n## ', '\n', 'Heading'], bold: ['**', '**', 'bold text'], italic: ['*', '*', 'italic text'],
    link: ['[', '](https://example.com)', 'link text'], list: ['\n- ', '\n', 'List item'],
    quote: ['\n> ', '\n', 'Quoted text'], code: ['\n```text\n', '\n```\n', 'Your code here'],
    table: ['\n', '\n', '| Heading | Heading |\n| --- | --- |\n| Value | Value |']
  };
  function insert(before, after, placeholder) {
    const editor = $('post-body'); const start = editor.selectionStart, end = editor.selectionEnd;
    const selected = editor.value.slice(start, end) || placeholder;
    editor.setRangeText(before + selected + after, start, end, 'end');
    editor.focus(); editor.setSelectionRange(start + before.length, start + before.length + selected.length); changed();
  }
  document.querySelectorAll('[data-format]').forEach(button => button.addEventListener('click', () => insert(...formats[button.dataset.format])));
  const starters = {
    lesson: '## What I wanted to understand\n\n\n## What I tried\n\n\n## What I learned\n\n\n## Next steps\n',
    blog: '## The starting point\n\n\n## My experience\n\n\n## Looking back\n',
    review: '## What I used\n\n\n## What worked well\n\n\n## What could be better\n\n\n## My verdict\n'
  };
  $('starter').addEventListener('change', () => { const text = starters[$('starter').value]; if (text) insert('\n', '\n', text); $('starter').value = ''; });
  fields.forEach(id => $(id).addEventListener('input', () => {
    if (id === 'post-slug') manualSlug = true;
    if (id === 'post-title' && !current?.revision && !manualSlug) $('post-slug').value = slug($('post-title').value);
    changed();
  }));
  $('post-search').addEventListener('input', renderList);
  $('post-state').addEventListener('change', renderList);
  $('new-post').addEventListener('click', () => { if (mayLeave()) { clearRecovery(); fill(null); $('post-title').focus(); } });
  for (const mode of ['write', 'preview', 'split']) $(`${mode}-view`).addEventListener('click', () => view(mode));
  $('post-form').addEventListener('submit', async event => {
    event.preventDefault(); if (busy || !$('post-form').reportValidity()) return;
    busy = true; $('save-post').disabled = true;
    const submitted = payload(); status('Saving…');
    try {
      const result = await api('save', submitted);
      // Do not erase keystrokes entered while a save request was in flight.
      const unchanged = JSON.stringify(payload()) === JSON.stringify(submitted);
      current = result;
      const savedSection = result.path.split('/').slice(0, -1).join('/');
      ensureSection(savedSection); $('post-section').value = savedSection;
      $('post-slug').value = result.path.split('/').pop().replace(/\.md$/, '');
      $('post-section').disabled = true; $('post-slug').readOnly = true;
      $('document-label').textContent = `content/${result.path}`;
      if (unchanged) { dirty = false; clearRecovery(); status(`${result.metadata.draft ? 'Draft' : 'Post'} saved to your website folder`); }
      else { dirty = true; remember(); }
      await refreshList();
    } catch (error) { status(error.message, true); }
    finally { busy = false; $('save-post').disabled = false; }
  });
  $('build-site').addEventListener('click', async () => {
    if (busy) return;
    if (dirty) { status('Save your changes before building the site.', true); return; }
    busy = true; $('build-site').disabled = true; status('Building the local site…');
    try { const result = await api('build', {}); status(`Built ${result.pages} pages. Use View site to check the result. Drafts are excluded.`); }
    catch (error) { status(error.message, true); }
    finally { busy = false; $('build-site').disabled = false; }
  });
  $('download-post').addEventListener('click', () => {
    const draft = payload();
    // A JSON object is valid YAML, preserving strings and punctuation exactly.
    const text = `---\n${JSON.stringify(draft.metadata, null, 2)}\n---\n\n${draft.body}\n`;
    const url = URL.createObjectURL(new Blob([text], {type: 'text/markdown;charset=utf-8'}));
    const link = document.createElement('a'); link.href = url; link.download = `${$('post-slug').value || 'untitled-post'}.md`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  $('desk-theme').addEventListener('change', () => {
    document.documentElement.dataset.theme = $('desk-theme').value;
    try { localStorage.setItem('kaz-interface-theme', $('desk-theme').value); } catch { /* Session works. */ }
    if (document.querySelector('.compose-surface').dataset.view !== 'write') preview();
  });
  window.addEventListener('beforeunload', event => { if (dirty || busy) { event.preventDefault(); event.returnValue = ''; } });
  document.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') { event.preventDefault(); $('post-form').requestSubmit(); }
    if ((event.ctrlKey || event.metaKey) && event.target === $('post-body') && ['b', 'i'].includes(event.key.toLowerCase())) {
      event.preventDefault(); insert(...formats[event.key.toLowerCase() === 'b' ? 'bold' : 'italic']);
    }
  });
  let recovery;
  try {
    const savedTheme = localStorage.getItem('kaz-interface-theme');
    if (['balanced', 'halo', 'resident'].includes(savedTheme)) { $('desk-theme').value = savedTheme; document.documentElement.dataset.theme = savedTheme; }
    recovery = JSON.parse(localStorage.getItem(recoveryKey) || 'null');
  } catch { /* Saving to files still works. */ }
  $('recover').addEventListener('click', () => {
    if (!recovery?.document || !mayLeave()) return;
    fill(recovery.document.revision ? recovery.document : null);
    ensureSection(recovery.values['post-section']);
    for (const id of fields) if (typeof recovery.values[id] === 'string') $(id).value = recovery.values[id];
    manualSlug = true; dirty = true; count(); $('recovery').hidden = true;
    status('Recovered unsaved text. Review it and save when ready.');
  });
  $('dismiss-recovery').addEventListener('click', () => { if (window.confirm('Discard this browser recovery copy?')) clearRecovery(); });
  fill(null);
  if (recovery?.document && recovery?.values) $('recovery').hidden = false;
  refreshList().catch(error => status(`Could not load your pages: ${error.message}`, true));
})();
