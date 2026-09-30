const {JSDOM} = require('../.cache/runtime-tests/node_modules/jsdom');
const {readFileSync} = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const base = path.join(__dirname, '../build');
const script = readFileSync(path.join(__dirname, 'site.js'), 'utf8');
const themeScript = readFileSync(path.join(__dirname, 'theme.js'), 'utf8');
const index = JSON.parse(readFileSync(path.join(base, 'search-index.json'), 'utf8'));
let passed = 0;
const tick = () => new Promise(resolve => setTimeout(resolve, 0));
function page(route='search/index.html', options={}) {
  const dom = new JSDOM(readFileSync(path.join(base, route), 'utf8'), {url:'https://example.test/search/', runScripts:'outside-only'});
  dom.window.fetch = options.fetch || (async () => ({ok:true, json:async()=>index}));
  if (options.storageBlocked) Object.defineProperty(dom.window, 'localStorage', {get(){throw Error('blocked');}});
  dom.window.eval(themeScript); dom.window.eval(script);
  return dom;
}
async function test(name, run) {
  await run(); passed++; console.log('PASS ' + name);
}
async function search(dom, value) {
  const doc=dom.window.document; doc.querySelector('#query').value=value;
  doc.querySelector('#search-form').dispatchEvent(new dom.window.Event('submit',{cancelable:true}));
  await tick(); return doc;
}
(async()=>{
  const cases = [
    ['exact title','C# Lesson 1','/learning/c-sharp/posts/c-sharp-lesson-1/'],
    ['partial title','Lesson 2','/learning/c-sharp/posts/c-sharp-lesson-2/'],
    ['case insensitive','c# LESSON 1','/learning/c-sharp/posts/c-sharp-lesson-1/'],
    ['surrounding whitespace','   Lesson 2   ','/learning/c-sharp/posts/c-sharp-lesson-2/'],
    ['internal whitespace','Lesson    2','/learning/c-sharp/posts/c-sharp-lesson-2/'],
    ['body-only term','myFriendsName','/learning/c-sharp/posts/c-sharp-lesson-1/'],
    ['tag matches','c sharp','/learning/c-sharp/posts/c-sharp-lesson-1/'],
    ['punctuation','Console.WriteLine()','/learning/c-sharp/posts/c-sharp-lesson-1/'],
    ['unicode','Schwarzmüller','/learning/courses/angular-guide/'],
    ['course instructor','Panjuta','/learning/courses/c-sharp-masterclass/'],
    ['project limitation','full functionality','/work/projects/space-invaders/']
  ];
  for(const [name,query,url] of cases) await test(name,async()=>{
    const dom=page();const doc=await search(dom,query);
    assert(doc.querySelector(`#search-results a[href="${url}"]`));dom.window.close();
  });
  await test('empty query does not fetch',async()=>{let calls=0;const dom=page(undefined,{fetch:()=>{calls++;}});const doc=await search(dom,' ');assert.equal(calls,0);assert.match(doc.querySelector('#search-status').textContent,/Enter a word/);dom.window.close();});
  await test('no results honest state',async()=>{const dom=page();const doc=await search(dom,'nonexistentxyzz');assert.match(doc.querySelector('#search-status').textContent,/No pages match/);assert.equal(doc.querySelectorAll('#search-results li').length,0);dom.window.close();});
  await test('markup query cannot execute',async()=>{const dom=page();const doc=await search(dom,'<img src=x onerror=alert(1)>');assert.equal(doc.querySelectorAll('#search-results img').length,0);dom.window.close();});
  await test('load failure then retry',async()=>{let fail=true;const dom=page(undefined,{fetch:async()=>{if(fail)throw Error('offline');return{ok:true,json:async()=>index};}});const doc=await search(dom,'Lesson');assert.equal(doc.querySelector('#search-retry').hidden,false);fail=false;doc.querySelector('#search-retry').click();await tick();assert.equal(doc.querySelector('#search-retry').hidden,true);assert(doc.querySelector('#search-results a'));dom.window.close();});
  await test('non-OK response exposes recovery',async()=>{const dom=page(undefined,{fetch:async()=>({ok:false})});const doc=await search(dom,'x');assert.equal(doc.querySelector('#search-retry').hidden,false);dom.window.close();});
  await test('malformed index exposes recovery',async()=>{const dom=page(undefined,{fetch:async()=>({ok:true,json:async()=>({})})});const doc=await search(dom,'x');assert.equal(doc.querySelector('#search-retry').hidden,false);dom.window.close();});
  await test('unsafe result URLs excluded and text escaped',async()=>{const data=[{title:'<img onerror=x>',url:'/about/',text:'query'},{title:'bad',url:'//evil.test',text:'query'},{title:'bad',url:'javascript:alert(1)',text:'query'}];const dom=page(undefined,{fetch:async()=>({ok:true,json:async()=>data})});const doc=await search(dom,'query');assert.equal(doc.querySelectorAll('#search-results a').length,1);assert.equal(doc.querySelectorAll('#search-results img').length,0);dom.window.close();});
  await test('latest query wins a delayed response',async()=>{let resolve;const waiting=new Promise(r=>resolve=r);const dom=page(undefined,{fetch:()=>waiting});await search(dom,'Steam');await search(dom,'Lesson 2');resolve({ok:true,json:async()=>index});await tick();const doc=dom.window.document;assert(doc.querySelector('#search-results a[href="/learning/c-sharp/posts/c-sharp-lesson-2/"]'));assert(!doc.querySelector('#search-results a[href="/personal/misc/writing/posts/steam-viz/"]'));dom.window.close();});
  await test('clear invalidates delayed response',async()=>{let resolve;const waiting=new Promise(r=>resolve=r);const dom=page(undefined,{fetch:()=>waiting});await search(dom,'Steam');dom.window.document.querySelector('#search-form').reset();resolve({ok:true,json:async()=>index});await tick();assert.equal(dom.window.document.querySelectorAll('#search-results li').length,0);dom.window.close();});
  await test('duplicate titles keep distinct valid routes',async()=>{const data=[{title:'Note',url:'/a/',text:'practice'},{title:'Note',url:'/b/',text:'practice'}];const dom=page(undefined,{fetch:async()=>({ok:true,json:async()=>data})});const doc=await search(dom,'practice');assert.deepEqual([...doc.querySelectorAll('#search-results a')].map(a=>a.getAttribute('href')),['/a/','/b/']);dom.window.close();});
  await test('large index remains searchable',async()=>{const data=Array.from({length:10000},(_,i)=>({title:'Note '+i,url:'/note/'+i+'/',text:'practice '+i}));const dom=page(undefined,{fetch:async()=>({ok:true,json:async()=>data})});const doc=await search(dom,'9999');assert.equal(doc.querySelectorAll('#search-results a').length,1);dom.window.close();});
  for(const value of ['balanced','forerunner','resident']) await test('theme '+value,async()=>{const dom=page('index.html');const select=dom.window.document.querySelector('#theme');select.value=value;select.dispatchEvent(new dom.window.Event('change'));assert.equal(dom.window.document.documentElement.dataset.theme,value);assert.equal(dom.window.localStorage.getItem('kaz-theme-v6'),value);dom.window.document.documentElement.dataset.theme='balanced';dom.window.eval(themeScript);assert.equal(dom.window.document.documentElement.dataset.theme,value);dom.window.close();});
  await test('blocked storage leaves themes usable',async()=>{const dom=page('index.html',{storageBlocked:true});const select=dom.window.document.querySelector('#theme');select.value='resident';select.dispatchEvent(new dom.window.Event('change'));assert.equal(dom.window.document.documentElement.dataset.theme,'resident');dom.window.close();});
  await test('escape closes mobile menu and restores focus',async()=>{const dom=page('index.html');const menu=dom.window.document.querySelector('.mobile-nav');menu.open=true;dom.window.document.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Escape'}));assert.equal(menu.open,false);assert.equal(dom.window.document.activeElement,menu.querySelector('summary'));dom.window.close();});
  for(const [route,query] of [['personal/anime/index.html','Horimiya'],['personal/misc/phasmophobia/ghosts/index.html','Spirit'],['personal/misc/phasmophobia/items/index.html','EMF'],['personal/misc/phasmophobia/maps/index.html','Tanglewood'],['personal/games/index.html','playtime']]) await test('filter recovery '+route,async()=>{const dom=page(route);const doc=dom.window.document;const input=doc.querySelector('[data-filter]');input.value=query;input.dispatchEvent(new dom.window.Event('input'));assert(doc.querySelectorAll('[data-record]:not([hidden])').length>0);input.value='xyznonexistent';input.dispatchEvent(new dom.window.Event('input'));assert.equal(doc.querySelector('[data-filter-empty]').hidden,false);input.value='';input.dispatchEvent(new dom.window.Event('input'));assert.equal(doc.querySelectorAll('[data-record][hidden]').length,0);dom.window.close();});
  console.log(`${passed} runtime behaviours passed`);
})().catch(error=>{console.error(error);process.exitCode=1;});
