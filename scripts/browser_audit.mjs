import {spawn} from 'node:child_process';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const modules=path.join(root,'.cache/performance/node_modules');
const {chromium}=await import(pathToFileURL(path.join(modules,'playwright/index.mjs')));
const {default:AxeBuilder}=await import(pathToFileURL(path.join(modules,'@axe-core/playwright/dist/index.mjs')));
const output=path.join(root,'.cache/browser-audit');await mkdir(output,{recursive:true});
const python=process.env.WEBSITE_PYTHON || path.join(root,'.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
const server=spawn(python,[path.join(root,'successor/serve.py')],{stdio:['ignore','pipe','inherit']});
await new Promise((resolve,reject)=>{server.stdout.once('data',resolve);server.once('error',reject);server.once('exit',code=>reject(Error('Preview exited '+code)));});
let browser;
const rows=[],errors=[],flows=[];
const routes=['/','/learning/','/learning/c-sharp/posts/c-sharp-blog-1/','/personal/games/','/personal/anime/','/search/','/personal/misc/phasmophobia/ghosts/','/404.html'];
const viewports=[[320,568],[390,844],[430,932],[844,390],[768,1024],[1024,768],[1280,1024],[1920,1080],[2560,1080],[3440,1440],[5120,2160],[5120,1440]];
try {
  browser=await chromium.launch({...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{channel:'chrome'}),headless:true,args:[...(process.env.CI?['--no-sandbox']:[]),'--disable-dev-shm-usage',...(process.env.WEBSITE_BROWSER_SINGLE_PROCESS?['--no-zygote','--single-process']:[])]});
  for(const theme of ['balanced','forerunner','resident']){
    const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'block'});
    await context.addInitScript(value=>localStorage.setItem('kaz-theme-v6',value),theme);
    const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
    for(const route of routes){
      await page.goto('http://127.0.0.1:8765'+route);
      const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
      const overflows=[];
      for(const [width,height] of viewports){
        await page.setViewportSize({width,height});
        const actual=await page.evaluate(()=>document.documentElement.scrollWidth);
        if(actual>width+1)overflows.push({width,height,actual});
      }
      await page.setViewportSize({width:390,height:844});
      if(route==='/')await page.screenshot({path:path.join(output,theme+'-home.png'),fullPage:true});
      rows.push({theme,route,violations:axe.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),overflows});
      console.log(theme,route,'axe',axe.violations.length,'overflow',overflows.length);
    }
  }
  const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,serviceWorkers:'block'});
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  const cdp=await context.newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:150,downloadThroughput:1600*1024/8,uploadThroughput:750*1024/8,connectionType:'cellular4g'});
  await cdp.send('Emulation.setCPUThrottlingRate',{rate:6});
  await page.goto('http://127.0.0.1:8765/');
  await page.keyboard.press('Tab');assert.equal(await page.locator('.skip').evaluate(node=>node===document.activeElement),true);
  await page.keyboard.press('Enter');assert.equal(await page.locator('#main').evaluate(node=>node===document.activeElement),true);flows.push('Keyboard skip link');
  await page.locator('.mobile-nav summary').focus();await page.keyboard.press('Enter');assert.equal(await page.locator('.mobile-nav').evaluate(node=>node.open),true);
  await page.keyboard.press('Escape');assert.equal(await page.locator('.mobile-nav summary').evaluate(node=>node===document.activeElement),true);flows.push('Menu Enter/Escape and focus restoration');
  await page.locator('#theme').focus();await page.keyboard.press('Home');await page.keyboard.press('ArrowDown');await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');
  assert.equal(await page.locator('html').getAttribute('data-theme'),'resident');await page.reload();assert.equal(await page.locator('#theme').inputValue(),'resident');flows.push('Keyboard theme selection and persistence');
  await page.locator('.mobile-nav summary').click();await page.getByRole('navigation',{name:'Mobile navigation'}).getByRole('link',{name:'Work',exact:true}).click();await page.waitForURL('**/work/');flows.push('Mobile home to work');
  await page.locator('.search-link').click();await page.locator('#query').fill('C# Lesson 1');await page.getByRole('button',{name:'Search',exact:true}).click();
  await page.locator('#search-results a[href="/learning/c-sharp/posts/c-sharp-lesson-1/"]').click();await page.waitForURL('**/c-sharp-lesson-1/');await page.goBack();flows.push('Search to authored note and browser back');
  await page.locator('#query').fill('nonexistentxyz');await page.getByRole('button',{name:'Search',exact:true}).click();await page.locator('#search-status').filter({hasText:'No pages match'}).waitFor();
  await page.getByRole('button',{name:'Clear',exact:true}).click();assert.equal(await page.locator('#query').inputValue(),'');flows.push('No-results and clear');
  await page.route('**/search-index.json',route=>route.fulfill({status:503,body:'Unavailable'}));await page.reload();await page.locator('#query').fill('Lesson');await page.getByRole('button',{name:'Search',exact:true}).click();await page.locator('#search-retry').waitFor({state:'visible'});
  await page.unroute('**/search-index.json');await page.locator('#search-retry').click();await page.locator('#search-results li').first().waitFor();flows.push('Search failure and retry');
  await page.goto('http://127.0.0.1:8765/personal/games/');await page.locator('[data-filter]').fill('nonexistentxyz');await page.locator('[data-filter-empty]').waitFor({state:'visible'});await page.locator('[data-filter]').fill('');await page.locator('[data-record]').first().waitFor();
  await page.locator('.chart-description summary').first().click();assert.equal(await page.locator('.chart-description').first().evaluate(node=>node.open),true);
  const image=await page.locator('img').first().evaluate(node=>({src:node.currentSrc,width:node.naturalWidth}));assert(image.width>0);flows.push('Chart filter recovery, description disclosure and responsive image load');
  const imageURL=new URL(await page.locator('.chart-link').first().getAttribute('href'),page.url()).href;
  const imageResponse=await page.request.get(imageURL);assert.equal(imageResponse.status(),200);flows.push('Original full-size chart');
  // A halved desktop viewport checks the reflow required at 200% browser zoom.
  await page.setViewportSize({width:640,height:512});assert(await page.evaluate(()=>document.documentElement.scrollWidth)<=641);flows.push('200% equivalent desktop reflow');
  const allRoutes=[...new Set([...((await readFile(path.join(root,'build/sitemap.xml'),'utf8')).matchAll(/<loc>(.*?)<\/loc>/g))].map(match=>new URL(match[1]).pathname).concat(['/404.html','/offline.html']))];
  await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});await cdp.send('Emulation.setCPUThrottlingRate',{rate:1});await page.setViewportSize({width:320,height:568});
  for(const route of allRoutes){const response=await page.goto('http://127.0.0.1:8765'+route);assert(response.status()===200);assert(await page.evaluate(()=>document.documentElement.scrollWidth)<=321,'Overflow '+route);}
  flows.push(allRoutes.length+' canonical direct loads at 320px');
  const offlineContext=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'allow'});
  const offlinePage=await offlineContext.newPage();await offlinePage.goto('http://127.0.0.1:8765/');
  await offlinePage.waitForFunction(()=>navigator.serviceWorker.controller,{timeout:15000});
  await offlinePage.goto('http://127.0.0.1:8765/personal/games/');
  await offlinePage.waitForFunction(async()=>Boolean(await caches.match(location.href)),{timeout:15000});
  await offlineContext.setOffline(true);await offlinePage.reload();assert.match(await offlinePage.locator('h1').textContent(),/Games/);
  await offlinePage.goto('http://127.0.0.1:8765/learning/python/');assert.match(await offlinePage.locator('h1').textContent(),/offline/);
  flows.push('Real service-worker saved page and unsaved-page offline fallback');
} catch(error){errors.push(error.message);console.error(error);}
finally{if(browser)await browser.close();server.kill();await writeFile(path.join(output,'report.json'),JSON.stringify({rows,flows,errors,viewports,browser:process.env.CHROME_PATH||'installed Chrome'},null,2));}
process.exitCode=errors.length||rows.some(row=>row.violations.length||row.overflows.length)?1:0;
