/* DOM-level behaviour tests, not a substitute for visual browser testing.
   Install jsdom into an ignored QA directory; production needs no Node tooling.
   node tests/runtime.cjs /absolute/path/to/node_modules/jsdom */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require(process.argv[2] || path.resolve('.cache/runtime-tests/node_modules/jsdom'));
const root = path.resolve(__dirname, '..');
const script = name => fs.readFileSync(path.join(root, 'assets/js', name), 'utf8');
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

function page(route = '/') {
  const filename = route === '/' ? 'index.html' : route.replace(/^\//,'') + 'index.html';
  const dom = new JSDOM(fs.readFileSync(path.join(root,'dist',filename),'utf8'),
    {url:'https://kazumi7884.co.uk'+route, runScripts:'outside-only', pretendToBeVisual:true});
  const media = {matches:false,addEventListener(type,fn){this.changed=fn;}};
  dom.window.matchMedia = () => media;
  dom.media = media;
  return dom;
}
function change(dom, node, value, type='change') {
  node.value=value;
  node.dispatchEvent(new dom.window.Event(type,{bubbles:true}));
}
function start(dom) { dom.window.eval(script('site.js')); }

test('blocked storage never erases article content', () => {
  const dom=page('/learning/c-sharp/posts/c-sharp-blog-1/');
  const article=dom.window.document.querySelector('[data-article-body]');
  const authoredText=()=>Array.from(article.querySelectorAll('p,h2,h3,pre code')).map(n=>n.textContent);
  const before=authoredText();
  Object.defineProperty(dom.window,'localStorage',{get(){throw new Error('denied');}});
  dom.window.eval(script('theme-init.js'));start(dom);
  change(dom,dom.window.document.querySelector('#theme-select'),'balanced');
  assert.equal(dom.window.document.documentElement.dataset.theme,'balanced');
  assert.equal(dom.window.document.querySelector('[data-article-body]'),article);
  assert.deepEqual(authoredText(),before);
  dom.window.close();
});
test('invalid stored theme is ignored', () => {
  const dom=page();dom.window.localStorage.setItem('kaz-interface-theme','<script>');
  dom.window.eval(script('theme-init.js'));
  assert.equal(dom.window.document.documentElement.dataset.theme,'balanced');dom.window.close();
});
test('valid saved preference applies before enhancement', () => {
  const dom=page();dom.window.localStorage.setItem('kaz-interface-theme','balanced');
  dom.window.eval(script('theme-init.js'));start(dom);
  assert.equal(dom.window.document.querySelector('#theme-select').value,'balanced');dom.window.close();
});
test('cross-tab preference updates only the theme', () => {
  const dom=page();start(dom);const before=dom.window.document.querySelector('main');
  dom.window.dispatchEvent(new dom.window.StorageEvent('storage',{key:'kaz-interface-theme',newValue:'resident'}));
  assert.equal(dom.window.document.documentElement.dataset.theme,'resident');
  assert.equal(dom.window.document.querySelector('main'),before);dom.window.close();
});
test('menu opens and Escape restores focus', () => {
  const dom=page();start(dom);const d=dom.window.document;const menu=d.querySelector('.nav-toggle');
  menu.click();assert.equal(menu.getAttribute('aria-expanded'),'true');
  d.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Escape'}));
  assert.equal(menu.getAttribute('aria-expanded'),'false');assert.equal(d.activeElement,menu);dom.window.close();
});
test('outside click closes mobile navigation', () => {
  const dom=page();start(dom);const d=dom.window.document;d.querySelector('.nav-toggle').click();
  d.querySelector('h1').click();assert.equal(d.querySelector('.nav-toggle').getAttribute('aria-expanded'),'false');dom.window.close();
});
test('crossing viewport breakpoint resets menu state', () => {
  const dom=page();start(dom);const menu=dom.window.document.querySelector('.nav-toggle');menu.click();dom.media.changed();
  assert.equal(menu.getAttribute('aria-expanded'),'false');dom.window.close();
});
test('board filtering is case-insensitive and reports empty results', async () => {
  const dom=page('/learning/c-sharp/');start(dom);const d=dom.window.document;
  const board=d.querySelector('[data-filter-board]');
  const input=board.querySelector('[data-filter-query]');change(dom,input,'cONsOlE','input');await pause(160);
  assert.ok(board.querySelectorAll('[data-filter-item]:not([hidden])').length>0);
  change(dom,input,'zzzznoactualentry','input');await pause(160);
  assert.equal(board.querySelector('[data-filter-empty]').hidden,false);
  change(dom,input,'','input');await pause(160);assert.equal(board.querySelector('[data-filter-empty]').hidden,true);dom.window.close();
});
test('sorting preserves the original article nodes', () => {
  const dom=page('/learning/c-sharp/');start(dom);const d=dom.window.document;
  const board=d.querySelector('[data-filter-board]');
  const nodes=Array.from(board.querySelectorAll('[data-filter-item]'));
  change(dom,d.querySelector('[data-filter-sort]'),'title');
  const sorted=Array.from(board.querySelectorAll('[data-filter-item]'));
  assert.ok(sorted.every(node=>nodes.includes(node)));
  assert.deepEqual(sorted.map(n=>n.dataset.title),nodes.map(n=>n.dataset.title).sort((a,b)=>a.localeCompare(b,'en-GB')));dom.window.close();
});
test('anime status and score filters operate on the full snapshot', () => {
  const dom=page('/personal/anime/');start(dom);const d=dom.window.document;
  change(dom,d.querySelector('[data-filter-category]'),'completed');
  let visible=Array.from(d.querySelectorAll('[data-filter-item]:not([hidden])'));
  assert.ok(visible.length>0);assert.ok(visible.every(n=>n.dataset.category==='completed'));
  change(dom,d.querySelector('[data-filter-sort]'),'score');
  visible=Array.from(d.querySelectorAll('[data-filter-item]:not([hidden])'));
  assert.ok(visible.every((n,i)=>i===0 || Number(visible[i-1].dataset.score)>=Number(n.dataset.score)));dom.window.close();
});
test('copy link success uses the current post URL', async () => {
  const dom=page('/learning/c-sharp/posts/c-sharp-blog-1/');let copied;
  Object.defineProperty(dom.window.navigator,'clipboard',{value:{writeText:async text=>{copied=text;}}});start(dom);
  dom.window.document.querySelector('[data-copy-link]').click();await pause(0);
  assert.equal(copied,'https://kazumi7884.co.uk/learning/c-sharp/posts/c-sharp-blog-1/#post-body');
  assert.equal(dom.window.document.querySelector('[data-copy-link]').textContent,'Copied');dom.window.close();
});
test('clipboard failure provides a usable manual fallback', async () => {
  const dom=page('/learning/c-sharp/posts/c-sharp-blog-1/');start(dom);
  dom.window.document.querySelector('[data-copy-link]').click();await pause(0);
  assert.match(dom.window.document.querySelector('[data-copy-status]').textContent,/address bar/);dom.window.close();
});
test('search renders results as text and never inserts index markup', async () => {
  const dom=page('/search/');const d=dom.window.document;
  dom.window.fetch=async()=>({ok:true,json:async()=>[{title:'console <img src=x onerror=alert(1)>',description:'Console notes',text:'console',url:'/about/'}]});
  dom.window.eval(script('search.js'));change(dom,d.querySelector('#search-query'),'console');
  d.querySelector('#search-form').dispatchEvent(new dom.window.Event('submit',{cancelable:true}));await pause(0);
  assert.equal(d.querySelectorAll('#search-results img').length,0);
  assert.equal(d.querySelectorAll('#search-results article').length,1);
  assert.equal(new URL(dom.window.location.href).searchParams.get('q'),'console');dom.window.close();
});
test('search network failure is retryable', async () => {
  const dom=page('/search/');const d=dom.window.document;let calls=0;
  dom.window.fetch=async()=>{if(++calls===1)throw new Error('offline');return {ok:true,json:async()=>[]};};
  dom.window.eval(script('search.js'));change(dom,d.querySelector('#search-query'),'test');
  const submit=()=>d.querySelector('#search-form').dispatchEvent(new dom.window.Event('submit',{cancelable:true}));
  submit();await pause(0);assert.match(d.querySelector('#search-status').textContent,/retry/);
  submit();await pause(0);assert.equal(calls,2);assert.match(d.querySelector('#search-status').textContent,/0 matching/);dom.window.close();
});
test('latest query wins when the search index arrives late', async () => {
  const dom=page('/search/');const d=dom.window.document;let resolve;
  dom.window.fetch=()=>new Promise(done=>{resolve=done;});dom.window.eval(script('search.js'));
  const submit=value=>{change(dom,d.querySelector('#search-query'),value);d.querySelector('#search-form').dispatchEvent(new dom.window.Event('submit',{cancelable:true}));};
  submit('old');submit('new');resolve({ok:true,json:async()=>[{title:'Old post',description:'old',text:'old',url:'/about/'},{title:'New post',description:'new',text:'new',url:'/blog/'}]});await pause(0);
  assert.match(d.querySelector('#search-results').textContent,/New post/);assert.doesNotMatch(d.querySelector('#search-results').textContent,/Old post/);dom.window.close();
});
