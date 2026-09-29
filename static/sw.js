const CACHE_PREFIX='kaz-notebook-';
const CORE_CACHE=CACHE_PREFIX+'core-v5.7';
const RUNTIME_CACHE=CACHE_PREFIX+'runtime-v5.7';
const CORE=['/','/offline.html','/site.webmanifest','/search-index.json'];

const sameOrigin=request=>new URL(request.url).origin===self.location.origin;
const cacheable=response=>response&&response.ok&&response.type!=='opaque';

async function put(cacheName,request,response){
  if(cacheable(response))await (await caches.open(cacheName)).put(request,response.clone());
  return response;
}

async function networkFirst(request){
  try{
    const response=await fetch(request);
    if(sameOrigin(request))await put(RUNTIME_CACHE,request,response);
    return response;
  }catch{
    const cached=await caches.match(request);
    if(cached)return cached;
    if(request.mode==='navigate')return caches.match('/offline.html');
    return Response.error();
  }
}

async function staleWhileRevalidate(request){
  const cached=await caches.match(request);
  const network=fetch(request)
    .then(response=>sameOrigin(request)?put(RUNTIME_CACHE,request,response):response)
    .catch(()=>null);
  return cached||(await network)||Response.error();
}

self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CORE_CACHE).then(cache=>cache.addAll(CORE)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate',event=>{
  event.waitUntil(
    caches.keys()
      .then(keys=>Promise.all(keys.filter(key=>key.startsWith(CACHE_PREFIX)&&key!==CORE_CACHE&&key!==RUNTIME_CACHE).map(key=>caches.delete(key))))
      .then(()=>self.clients.claim())
  );
});

self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET'||!sameOrigin(request)||request.headers.has('range'))return;
  const url=new URL(request.url);
  if(request.mode==='navigate'||url.pathname==='/search-index.json'){
    event.respondWith(networkFirst(request));
    return;
  }
  if(['style','script','image','font'].includes(request.destination)){
    event.respondWith(staleWhileRevalidate(request));
  }
});
