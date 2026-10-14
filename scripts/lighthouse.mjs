import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const phase=process.argv[2] || 'after';
if(!/^[a-z0-9-]+$/i.test(phase)) throw Error('Use a simple report label, such as before or after.');
const source=path.resolve(process.argv[3] || root);
const modules=path.join(root,'.cache/performance/node_modules');
const {default:lighthouse}=await import(pathToFileURL(path.join(modules,'lighthouse/core/index.js')));
const launcher=await import(pathToFileURL(path.join(modules,'chrome-launcher/dist/index.js')));
const python=process.env.WEBSITE_PYTHON || path.join(root,'.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
if(!existsSync(path.join(source,'build/index.html'))) throw Error('Build the selected production source before auditing.');
const output=path.join(root,'.cache/lighthouse',phase);await mkdir(output,{recursive:true});
const routes=[['home','/'],['games','/personal/games/'],['steam-study','/personal/misc/writing/posts/steam-viz/'],['ghosts','/personal/misc/phasmophobia/ghosts/']];
const server=spawn(python,[path.join(root,'successor/serve.py'),'--port','8765','--directory',path.join(source,'build')],{stdio:['ignore','pipe','inherit']});
await new Promise((resolve,reject)=>{server.stdout.once('data',resolve);server.once('error',reject);server.once('exit',code=>reject(Error('Preview exited '+code)));});
const summary=[];let blocked=false;
try {
  for(const [name,route] of routes){
    const samples=[];
    for(let run=1;run<=3;run++){
      const chrome=await launcher.launch({chromePath:process.env.CHROME_PATH,chromeFlags:['--headless','--disable-dev-shm-usage',...(process.env.CI?['--no-sandbox']:[])]});
      try{
        const result=await lighthouse('http://127.0.0.1:8765'+route,{port:chrome.port,logLevel:'error',onlyCategories:['performance','accessibility','best-practices','seo'],formFactor:'mobile',throttlingMethod:'simulate'});
        const {lhr}=result;
        await writeFile(path.join(output,`${name}-${run}.json`),JSON.stringify(lhr));
        const score=category=>lhr.categories[category].score===null?null:Math.round(lhr.categories[category].score*100);
        const metrics={performance:score('performance'),accessibility:score('accessibility'),bestPractices:score('best-practices'),seo:score('seo'),LCP:lhr.audits['largest-contentful-paint'].numericValue??null,FCP:lhr.audits['first-contentful-paint'].numericValue??null,TBT:lhr.audits['total-blocking-time'].numericValue??null,CLS:lhr.audits['cumulative-layout-shift'].numericValue??null,bytes:lhr.audits['total-byte-weight'].numericValue??null};
        const errors=Object.entries(lhr.audits).filter(([,audit])=>audit.errorMessage).map(([id,audit])=>({id,error:audit.errorMessage}));
        if(lhr.runtimeError||metrics.performance===null) blocked=true;
        samples.push(metrics);
        console.log(JSON.stringify({phase,route,run,metrics,errors,browser:lhr.userAgent,lighthouse:lhr.lighthouseVersion}));
      }finally{await chrome.kill();}
    }
    const median=Object.fromEntries(Object.keys(samples[0]).map(key=>[key,samples.some(row=>row[key]===null)?null:samples.map(row=>row[key]).sort((a,b)=>a-b)[1]]));
    summary.push({name,route,samples,median});
    await writeFile(path.join(output,'summary.json'),JSON.stringify({status:blocked?'BLOCKED':'MEASURED',summary},null,2));
  }
}finally{server.kill();}
process.exitCode=blocked?1:0;
