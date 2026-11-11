const { chromium } = require(process.env.FREEWILL_PLAYWRIGHT || 'playwright');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {createInterface} = require('node:readline');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');
const artifacts = process.env.FREEWILL_ARTIFACTS || fs.mkdtempSync(path.join(os.tmpdir(), 'freewill-brain-browser-'));
fs.mkdirSync(artifacts, {recursive:true});
(async () => {
  const fixture = spawn(process.env.PYTHON || 'python', ['-u', path.join(__dirname, 'smoke-server.py')], {stdio:['pipe','pipe','pipe']});
  let fixtureErrors='';
  fixture.stderr.on('data',chunk=>{fixtureErrors=(fixtureErrors+chunk.toString()).slice(-10000);});
  let browser;
  try {
    const base = await new Promise((resolve,reject)=>{
      const timer = setTimeout(()=>reject(Error('fixture startup timed out')),15000);
      fixture.once('error',reject);
      createInterface({input:fixture.stdout}).on('line',line=>{
        if(line.startsWith('http://127.0.0.1:')) { clearTimeout(timer);resolve(line); }
      });
      fixture.once('exit',code=>{clearTimeout(timer);reject(Error('fixture exited: '+code));});
    });
    browser = await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE_PATH || undefined,headless:true,
      args:['--enable-unsafe-swiftshader',...(process.env.FREEWILL_NO_SANDBOX==='1'?['--no-sandbox']:[])]});
    const context = await browser.newContext({viewport:{width:1440,height:960},locale:'fr-FR',colorScheme:'dark'});
    const page = await context.newPage();
    const errors=[], consoleErrors=[], calls=[], httpFailures=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});
    page.on('request',r=>calls.push(r.url()));
    page.on('response',r=>{if(r.status()>=400)httpFailures.push({url:r.url(),status:r.status()});});
    await page.addInitScript(() => {
      // The interface is English unless French was chosen; this audit reads French labels.
      try { localStorage.setItem('fw-lang', 'fr'); } catch (_) {}
      let current;
      window.__brainInstances=[]; window.__brainEvents=[];
      Object.defineProperty(window,'Brain',{configurable:true,get(){return current},set(Original){
        current = class extends Original { constructor(...args){super(...args);window.__auditBrain=this;window.__brainInstances.push(this);
          for (const key of ['stage','recall','decision','speech','read','dream','remember']) { const original=this[key]; if(original)this[key]=(...a)=>{window.__brainEvents.push({key,args:a});return original.apply(this,a)}; }
        }};
      }});
    });
    await page.goto(base);
    await page.getByRole('button',{name:'Cerveau',exact:true}).click();
    await page.waitForFunction(()=>window.__auditBrain?.counts?.memories>=36);
    await page.waitForTimeout(300);
    const initial=await page.evaluate(()=>({webgl:window.__auditBrain.capabilities.webgl,points:window.__auditBrain.tissue.pts.length,counts:window.__auditBrain.counts,objects:window.__auditBrain.scene?.children.length}));
    assert.equal(initial.webgl,true);
    await page.locator('.brain-core-label[data-brain-id="@self"]').waitFor({state:'visible'});
    const visibleLabels=await page.evaluate(()=>{
      const visible=(element)=>{
        const style=getComputedStyle(element),box=element.getBoundingClientRect();
        return style.display!=='none'&&style.visibility!=='hidden'&&Number(style.opacity)>.1&&
          box.width>0&&box.height>0&&box.left<innerWidth&&box.right>0&&box.top<innerHeight&&box.bottom>0;
      };
      const core=document.querySelector('.brain-core-label[data-brain-id="@self"]');
      const memories=[...document.querySelectorAll('.brain-memory-label[data-brain-id]')].filter(visible)
        .map(element=>({id:element.dataset.brainId,title:element.textContent,
          realTitle:window.__auditBrain.nodes.get(element.dataset.brainId)?.title}));
      return {coreVisible:!!core&&visible(core),memories};
    });
    assert.equal(visibleLabels.coreVisible,true,'the core remains explicitly labelled in the rendered view');
    assert.ok(visibleLabels.memories.length>=3,'at least three real memories are labelled without hovering');
    for(const label of visibleLabels.memories)assert.ok(label.realTitle&&label.title.includes(label.realTitle),'a memory label must name its real memory');
    await page.getByRole('button',{name:'Rotation',exact:true}).click();
    const api=async(path,body)=>page.evaluate(async({path,body})=>{
      const response=await fetch(path,{method:body===undefined?'GET':'POST',headers:{'X-Freewill-Token':document.querySelector('meta[name="freewill-token"]').content,'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
      if(!response.ok)throw Error(await response.text());return response.json();
    },{path,body});
    await api('/api/settings',{thoughts_per_hour:0});
    await api('/api/message',{text:'Je me souviens de la mer, des vagues et de notre rencontre.'});
    await page.waitForFunction(()=>window.__brainEvents.some(e=>e.key==='remember'));
    await page.waitForFunction(()=>window.__auditBrain.counts.memories>=37);
    const data=await api('/api/memory');
    const after=await page.evaluate(()=>({counts:window.__auditBrain.counts,events:window.__brainEvents.map(e=>e.key),signals:window.__auditBrain.signals.filter(Boolean).length,waves:window.__auditBrain.waves.length,status:document.querySelector('.brain-status').textContent,edges:window.__auditBrain.edges.filter(e=>e.kind==='memory')}));
    for(const edge of after.edges){const a=data.memories.find(m=>m.id===edge.from),b=data.memories.find(m=>m.id===edge.to);assert.ok(a?.links.includes(edge.to)||b?.links.includes(edge.from));}
    assert.ok(after.events.includes('recall'));assert.ok(after.events.includes('speech'));assert.ok(after.signals>0);
    await page.getByRole('button',{name:'Figer la vue',exact:true}).click();
    const frozen=await page.evaluate(()=>window.__auditBrain.time);
    await page.waitForTimeout(250);
    assert.equal(await page.evaluate(()=>window.__auditBrain.time),frozen);
    // Compare themes on the very same real event, geometry and camera state.
    await page.screenshot({path:path.join(artifacts,'brain-visible-dark.png'),fullPage:true});
    await page.evaluate(()=>{document.documentElement.dataset.theme='light';window.__auditBrain.setTheme()});
    await page.screenshot({path:path.join(artifacts,'brain-visible-light.png'),fullPage:true});
    await page.getByRole('button',{name:'Figer la vue',exact:true}).click();
    await page.waitForTimeout(4500);
    const idle=await page.evaluate(()=>({signals:window.__auditBrain.signals.filter(Boolean).length,waves:window.__auditBrain.waves.length}));
    assert.equal(idle.signals,0);assert.equal(idle.waves,0);
    await api('/api/sleep',{});
    await page.waitForFunction(()=>window.__brainEvents.some(e=>e.key==='dream'));
    await page.waitForFunction(()=>window.__auditBrain.snapshot.sleeping===false);
    const candidate=await page.evaluate(()=>{
      const b=window.__auditBrain,box=b.canvas.getBoundingClientRect();
      for(const node of b.nodes.values())if(node.kind==='memory'){
        const p=new b.THREE.Vector3(...node.p).project(b.camera),x=box.left+(p.x*.5+.5)*box.width,y=box.top+(-p.y*.5+.5)*box.height;
        b.pick({clientX:x,clientY:y});if(b.hover?.id===node.id)return{x,y,id:node.id};
      }return null;
    });
    assert.ok(candidate,'at least one memory can be selected');
    await page.mouse.click(candidate.x,candidate.y);
    await page.waitForSelector('.memory');
    await page.waitForSelector('.mem-body');
    await page.getByRole('button',{name:'Cerveau',exact:true}).click();
    await page.waitForFunction(()=>window.__auditBrain.running);
    assert.equal(await page.locator('.brain-world-labels').count(),1);
    assert.equal(await page.evaluate(()=>window.__brainInstances.slice(0,-1).every(b=>!b.running)),true);
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.waitForFunction(()=>window.__auditBrain.reduced===true);
    await page.setViewportSize({width:1000,height:760});
    await page.screenshot({path:path.join(artifacts,'brain-visible-compact.png'),fullPage:true});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.route('**/three.bundle.js',route=>route.fulfill({contentType:'application/javascript',body:'/* unavailable for fallback test */'}));
    await page.reload();await page.getByRole('button',{name:'Cerveau',exact:true}).click();
    await page.waitForFunction(()=>window.__auditBrain?.capabilities?.webgl===false);
    const fallback=await page.evaluate(()=>({webgl:window.__auditBrain.capabilities.webgl,canvas2d:!!window.__auditBrain.ctx}));
    assert.equal(fallback.canvas2d,true);
    console.log(JSON.stringify({artifacts,initial,visibleLabels,after:{...after,edges:after.edges.length},idle,fallback,errors,consoleErrors,httpFailures,fixtureErrors,externalRequests:calls.filter(u=>!u.startsWith(base+'/'))}));
    assert.deepEqual(errors,[]);assert.deepEqual(consoleErrors,[]);
    assert.deepEqual(httpFailures,[]);assert.equal(fixtureErrors.includes('Traceback'),false,fixtureErrors);
  } finally {
    if(browser)await browser.close();
    fixture.stdin.end();
    await new Promise(resolve=>{
      const timer=setTimeout(()=>{fixture.kill();resolve();},3000);
      fixture.once('exit',()=>{clearTimeout(timer);resolve();});
    });
  }
})().catch(e=>{console.error(e);process.exitCode=1});
