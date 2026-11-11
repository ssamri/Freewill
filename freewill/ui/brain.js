// Freewill's brain is an event-driven instrument, not a model of LLM neurons.
// Cyan tissue is illustrative. Memories, their links, and the events that
// illuminate them come from the running being. Three.js is bundled locally.
(function () {
  "use strict";

  const SOURCE_COLOR = {
    message: [0.31, 0.77, 0.97], reminiscence: [1, 0.64, 0.28], need: [1, 0.43, 0.59],
    question: [0.77, 0.55, 1], association: [0.37, 0.84, 0.64], drift: [0.59, 0.63, 0.78],
    reading: [0.50, 0.83, 0.79], dream: [0.72, 0.49, 1],
  };
  const SOURCE_AT = {
    message: [0.0, 0.04, 0.94], question: [-0.29, 0.65, 0.26], association: [0.74, 0.24, -0.12],
    reminiscence: [-0.76, -0.12, 0.10], need: [0, -0.58, 0.06], drift: [0.56, -0.29, -0.66],
    reading: [-0.54, 0.30, -0.72], dream: [0, -0.25, -1.02],
  };
  const PALETTE = [[0.49, 0.62, 1], [1, 0.62, 0.36], [0.32, 0.86, 0.87], [0.82, 0.58, 1],
                   [0.48, 0.87, 0.63], [1, 0.54, 0.69], [0.91, 0.79, 0.41], [0.43, 0.70, 1]];
  const SELF_COLOR = [0.86, 0.68, 1], MAX_WAVES = 10, MAX_SIGNALS = 220, TAIL = 8;
  const clamp = (x, a, b) => Math.max(a, Math.min(b, Number.isFinite(x) ? x : a));
  const now = () => performance.now();
  function hash(s) {
    let h = 2166136261;
    for (let i = 0; i < String(s).length; i++) { h ^= String(s).charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function random(seed) {
    return () => {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function sourceKey(source) {
    if (String(source).startsWith("need")) return "need";
    if (source === "return") return "message";
    return SOURCE_AT[source] ? source : "drift";
  }
  const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
  function bezier(a, b, c, d, t, out) {
    const u = 1 - t;
    for (let k = 0; k < 3; k++) out[k] = u*u*u*a[k] + 3*u*u*t*b[k] + 3*u*t*t*c[k] + t*t*t*d[k];
    return out;
  }
  function curve(a, b, seed) {
    const r = random(seed), distance = Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]), bend = distance * (0.08 + r() * 0.12);
    return [a, mix(a, b, 0.33).map((v, i) => v + (r() - 0.5) * bend * (i === 1 ? 2 : 1)),
            mix(a, b, 0.66).map((v, i) => v + (r() - 0.5) * bend * (i === 1 ? 2 : 1)), b];
  }

  // A spatial grid keeps illustrative connectivity linear in tissue size.
  // No anatomical region or synthetic edge is presented as a real memory link.
  function buildTissue() {
    const rng = random(20461111), pts = [], cell = 0.18;
    function lobe(count, side, cx, cy, cz, rx, ry, rz) {
      let n = 0;
      while (n < count) {
        const y = 2 * rng() - 1, angle = rng() * Math.PI * 2, s = Math.sqrt(1 - y*y);
        const x = s * Math.cos(angle), z = s * Math.sin(angle);
        const groove = 1 + 0.046 * Math.sin(15*x + 8*z + 2*y) * Math.cos(12*y - 4*z)
                           + 0.025 * Math.sin(26*y + 9*z);
        const depth = rng() < 0.15 ? 0.64 + rng() * 0.22 : 0.96 + rng() * 0.04;
        const p = [cx + x*rx*groove*depth, cy + y*ry*groove*depth, cz + z*rz*groove*depth];
        if (side && p[0] * side < 0.045) continue;
        // Broad frontal pole, a softer taper at the occipital end.
        p[0] *= 1 + 0.055 * p[2];
        pts.push(p); n++;
      }
    }
    if (Array.isArray(window.FreewillBrainShape) && window.FreewillBrainShape.length) {
      // This static surface is the reference project's MIT-licensed brain mesh.
      // Centre/scale only: preserve its sulci, hemispheres and recognisable profile.
      for (const vertex of window.FreewillBrainShape) {
        pts.push([(vertex[0] + 0.555) / 75, (vertex[1] - 0.76) / 75, (vertex[2] - 14.725) / 75]);
      }
    } else {
      lobe(2400, -1, -0.40, 0.16, 0.00, 0.59, 0.72, 1.13);
      lobe(2400, 1, 0.40, 0.16, 0.00, 0.59, 0.72, 1.13);
      lobe(620, 0, 0, -0.57, -0.79, 0.61, 0.28, 0.40);
    }
    const grid = new Map(), edges = [], seen = new Set();
    const key = (x, y, z) => x + "," + y + "," + z;
    pts.forEach((p, i) => {
      const k = key(Math.floor(p[0]/cell), Math.floor(p[1]/cell), Math.floor(p[2]/cell));
      if (!grid.has(k)) grid.set(k, []); grid.get(k).push(i);
    });
    pts.forEach((p, i) => {
      const gx = Math.floor(p[0]/cell), gy = Math.floor(p[1]/cell), gz = Math.floor(p[2]/cell);
      const near = [];
      for (let x = -1; x <= 1; x++) for (let y = -1; y <= 1; y++) for (let z = -1; z <= 1; z++) {
        const group = grid.get(key(gx+x, gy+y, gz+z));
        if (!group) continue;
        for (const j of group) if (i !== j) {
          const q = pts[j], d = (p[0]-q[0])**2 + (p[1]-q[1])**2 + (p[2]-q[2])**2;
          if (d < 0.19**2) near.push([j, d]);
        }
      }
      near.sort((a, b) => a[1] - b[1]);
      for (let n = 0; n < Math.min(3, near.length); n++) {
        const j = near[n][0], id = Math.min(i,j) + ":" + Math.max(i,j);
        if (!seen.has(id)) { seen.add(id); edges.push([i,j]); }
      }
    });
    const fibres = [];
    for (const [i,j] of edges) {
      const path = curve(pts[i], pts[j], i*65537+j), a = [0,0,0], b = [0,0,0];
      bezier(...path, 0, a);
      for (let k = 1; k <= 2; k++) {
        bezier(...path, k/2, b); fibres.push(...a, ...b); a[0]=b[0]; a[1]=b[1]; a[2]=b[2];
      }
    }
    return { pts, fibres, grid, cell };
  }
  let tissueCache;

  const WAVE_GLSL = `
    uniform float uTime;
    uniform vec4 uWaveOrigin[${MAX_WAVES}];
    uniform vec4 uWaveColor[${MAX_WAVES}];
    uniform vec2 uWaveShape[${MAX_WAVES}];
    void waveAt(vec3 p, out float energy, out vec3 color) {
      energy = 0.0; color = vec3(0.0);
      for (int i=0; i<${MAX_WAVES}; i++) {
        float age = uTime - uWaveOrigin[i].w;
        float radius = uWaveShape[i].y;
        float front = age * uWaveShape[i].x;
        if (age >= 0.0 && front < radius + 0.25) {
          float d = distance(p, uWaveOrigin[i].xyz);
          float band = (d-front) / 0.14;
          float e = exp(-band*band*1.6) * uWaveColor[i].w * max(0.0, 1.0-d/radius);
          energy += e; color += uWaveColor[i].xyz * e;
        }
      }
      if (energy > 0.001) color /= energy;
    }
  `;
  const TISSUE_VERTEX = WAVE_GLSL + `
    attribute float aSize;
    uniform float uPixelRatio;
    uniform float uAmbient;
    uniform vec3 uBaseColor;
    varying vec3 vColor;
    varying float vEnergy;
    void main() {
      float e; vec3 c; waveAt(position, e, c);
      vEnergy = e;
      vColor = mix(uBaseColor, c, min(1.0, e*1.25));
      vec4 mv = modelViewMatrix * vec4(position, 1.0);
      gl_Position = projectionMatrix * mv;
      gl_PointSize = min(10.0, (aSize + min(1.0,e)*1.2) * uPixelRatio * (3.2/-mv.z));
    }
  `;
  const TISSUE_FRAGMENT = `
    uniform float uAmbient;
    varying vec3 vColor;
    varying float vEnergy;
    void main() {
      float r = length(gl_PointCoord - 0.5)*2.0;
      if (r > 1.0) discard;
      float halo = exp(-r*r*5.0);
      float core = exp(-r*r*40.0);
      float alpha = (uAmbient + min(1.0,vEnergy)*0.32) * (halo*0.5+core*0.7);
      gl_FragColor = vec4(mix(vColor, vec3(1.0), core*min(0.08,vEnergy*0.04)), alpha);
    }
  `;
  const FIBRE_VERTEX = WAVE_GLSL + `
    uniform vec3 uBaseColor;
    varying vec3 vColor;
    varying float vEnergy;
    void main() {
      float e; vec3 c; waveAt(position, e, c);
      vEnergy = e; vColor = mix(uBaseColor, c, min(1.0,e*1.8));
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0);
    }
  `;
  const FIBRE_FRAGMENT = `
    uniform float uLineOpacity;
    varying vec3 vColor;
    varying float vEnergy;
    void main() { gl_FragColor = vec4(vColor, uLineOpacity + min(0.18,vEnergy*0.12)); }
  `;
  const NODE_VERTEX = `
    attribute vec3 aColor;
    attribute float aSize;
    attribute float aEnergy;
    attribute float aKind;
    uniform float uPixelRatio;
    varying vec3 vColor;
    varying float vEnergy;
    varying float vVisible;
    varying float vKind;
    void main() {
      vColor=aColor; vEnergy=aEnergy; vVisible=step(0.1,aSize); vKind=aKind;
      vec4 mv=modelViewMatrix*vec4(position,1.0);
      gl_Position=projectionMatrix*mv;
      gl_PointSize=min(180.0, aSize*uPixelRatio*(3.2/-mv.z)*(1.0+min(aEnergy,1.0)*0.18));
    }
  `;
  const NODE_FRAGMENT = `
    uniform float uNodeOpacity;
    uniform float uLightTheme;
    varying vec3 vColor;
    varying float vEnergy;
    varying float vVisible;
    varying float vKind;
    void main() {
      if(vVisible<0.5) discard;
      float r=length(gl_PointCoord-0.5)*2.0;
      if(r>1.0) discard;
      vec3 base=mix(vColor,vColor*0.48,uLightTheme);
      vec3 paper=mix(vec3(0.025,0.032,0.065),vec3(0.97,0.97,1.0),uLightTheme);
      float halo=exp(-r*r*5.0);
      if(vKind>3.5) {
        float core=exp(-r*r*30.0);
        vec3 centre=mix(vec3(1.0),vColor*0.28,uLightTheme);
        gl_FragColor=vec4(mix(base,centre,core*0.8),(core+halo*0.5)*uNodeOpacity);
      } else {
        // A solid silhouette keeps real data distinct from the additive tissue.
        float isSelf=step(1.5,vKind)*(1.0-step(2.5,vKind));
        float bodyRadius=mix(vKind<0.5?0.30:0.23,0.29,isSelf);
        float body=1.0-smoothstep(bodyRadius-0.035,bodyRadius+0.025,r);
        float rim=1.0-smoothstep(0.018,0.04,abs(r-mix(0.46,0.52,isSelf)));
        float outer=(1.0-smoothstep(0.008,0.022,abs(r-0.78)))*isSelf;
        float backing=1.0-smoothstep(0.59,0.70,r);
        vec3 bead=mix(base,mix(vec3(1.0,0.96,0.87),base*0.65,uLightTheme),exp(-r*r*22.0)*0.65);
        vec3 color=mix(paper,bead,body);
        color=mix(color,base,max(rim,outer));
        float alpha=max(backing*0.98,max(rim,outer)*0.98)+halo*0.10;
        gl_FragColor=vec4(color,min(1.0,alpha)*uNodeOpacity);
      }
    }
  `;

  function fallback(canvas, tip, labels, options) {
    if (!window.BrainCanvas) throw new Error("Brain renderer is unavailable");
    // A canvas that acquired WebGL cannot subsequently acquire a 2D context.
    const replacement = canvas.cloneNode(false); canvas.replaceWith(replacement);
    const brain = new window.BrainCanvas(replacement, tip, labels, options);
    brain.capabilities = { webgl: false, controls: false };
    return brain;
  }

  class Brain {
    constructor(canvas, tip, labels, options) {
      if (!window.FreewillThree) return fallback(canvas, tip, labels, options);
      const { THREE, OrbitControls } = window.FreewillThree;
      this.THREE=THREE; this.canvas=canvas; this.tip=tip; this.labels=labels; this.options=options||{};
      this.capabilities={webgl:true, controls:true};
      this.running=true; this.time=0; this.last=now(); this.nodes=new Map(); this.edges=[];
      this.signals=new Array(MAX_SIGNALS).fill(null); this.nextSignal=0; this.pending=[]; this.waves=[];
      this.need=0; this.fatigue=0; this.asleep=false; this.pausedReason=""; this.hover=null;
      this.userControls={rotate:true,motion:true,paused:false};
      this.media=matchMedia("(prefers-reduced-motion: reduce)"); this.reduced=this.media.matches;
      this.resources=new Set(); this.labelsDOM=[]; this.memoryLoaded=false;
      try {
        this.renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true,powerPreference:"high-performance"});
        this.renderer.setPixelRatio(Math.min(1.75,window.devicePixelRatio||1));
        this.renderer.setClearColor(0x000000,0);
      } catch (error) {
        if (this.renderer) this.renderer.dispose();
        return fallback(canvas,tip,labels,options);
      }
      this.scene=new THREE.Scene();
      this.camera=new THREE.PerspectiveCamera(35,1,0.05,50);
      this.camera.position.set(3.15,0.78,2.15);
      this.controls=new OrbitControls(this.camera,canvas);
      this.controls.target.set(0,0.02,0); this.controls.enableDamping=true; this.controls.dampingFactor=0.075;
      this.controls.enablePan=false; this.controls.minDistance=2.35; this.controls.maxDistance=7;
      this.controls.minPolarAngle=0.24; this.controls.maxPolarAngle=Math.PI-0.24;
      this.controls.autoRotateSpeed=0.18;
      this.controls.update(); this.controls.saveState();
      this.raycaster=new THREE.Raycaster(); this.raycaster.params.Points.threshold=0.065;
      this.pointer=new THREE.Vector2(); this.projection=new THREE.Vector3();
      this.uniforms={
        uTime:{value:0},uPixelRatio:{value:this.renderer.getPixelRatio()},uAmbient:{value:0.76},
        uBaseColor:{value:new THREE.Color(0.10,0.56,0.76)},uLineOpacity:{value:0.19},uNodeOpacity:{value:1},uLightTheme:{value:0},
        uWaveOrigin:{value:Array.from({length:MAX_WAVES},()=>new THREE.Vector4(0,0,0,-1000))},
        uWaveColor:{value:Array.from({length:MAX_WAVES},()=>new THREE.Vector4())},
        uWaveShape:{value:Array.from({length:MAX_WAVES},()=>new THREE.Vector2(1,1))},
      };
      this.buildTissue(); this.buildFixed(); this.buildSignalPool(); this.rebuildNodes();
      this.labelLayer=document.createElement("div"); this.labelLayer.className="brain-world-labels";
      Object.assign(this.labelLayer.style,{position:"absolute",inset:"0",pointerEvents:"none",overflow:"hidden"});
      this.labelLayer.setAttribute("aria-hidden","true"); canvas.parentElement.appendChild(this.labelLayer);
      this.buildLabels();
      this.onMove=(event)=>this.pick(event);
      this.onDown=(event)=>{this.down={x:event.clientX,y:event.clientY};};
      this.onUp=(event)=>{
        const down=this.down;this.down=null;
        if(!down || Math.hypot(event.clientX-down.x,event.clientY-down.y)>5) return;
        this.pick(event);
        if(this.options.onInspect) this.options.onInspect(this.hover?this.info(this.hover):null);
        if(this.hover?.kind==="memory" && this.options.onOpen) this.options.onOpen(this.hover.id);
      };
      this.onLeave=()=>{this.hover=null; this.tip.hidden=true;};
      this.onVisibility=()=>{this.last=now();};
      this.onMedia=()=>{this.reduced=this.media.matches; this.last=now();};
      this.onLost=(event)=>{event.preventDefault(); this.contextLost=true; this.tip.hidden=false;
        this.tip.textContent=this.labels.contextLost||"3D paused — reload the page to restore graphics";};
      this.onRestored=()=>{this.contextLost=false; this.last=now(); this.tip.hidden=true;};
      canvas.addEventListener("pointermove",this.onMove);canvas.addEventListener("pointerdown",this.onDown);
      canvas.addEventListener("pointerup",this.onUp);canvas.addEventListener("pointerleave",this.onLeave);
      canvas.addEventListener("webglcontextlost",this.onLost);canvas.addEventListener("webglcontextrestored",this.onRestored);
      document.addEventListener("visibilitychange",this.onVisibility);this.media.addEventListener("change",this.onMedia);
      this.resizeObserver=new ResizeObserver(()=>this.resize());this.resizeObserver.observe(canvas);
      this.resize();this.setTheme();
      this.frame=this.frame.bind(this);this.raf=requestAnimationFrame(this.frame);
    }

    material(options) {
      const m=new this.THREE.ShaderMaterial({uniforms:this.uniforms,transparent:true,
        depthWrite:false,depthTest:false,blending:this.THREE.AdditiveBlending,...options});
      this.resources.add(m);return m;
    }
    geometry() { const g=new this.THREE.BufferGeometry();this.resources.add(g);return g; }
    attribute(geometry,name,array,size) {
      geometry.setAttribute(name,new this.THREE.BufferAttribute(array,size));
    }
    buildTissue() {
      const THREE=this.THREE,tissue=tissueCache||(tissueCache=buildTissue());this.tissue=tissue;
      const g=this.geometry(),sizes=new Float32Array(tissue.pts.length),rng=random(91);
      for(let i=0;i<sizes.length;i++) sizes[i]=1.0+rng()*0.9;
      this.attribute(g,"position",new Float32Array(tissue.pts.flat()),3);this.attribute(g,"aSize",sizes,1);
      this.tissuePoints=new THREE.Points(g,this.material({vertexShader:TISSUE_VERTEX,fragmentShader:TISSUE_FRAGMENT}));
      this.scene.add(this.tissuePoints);
      const f=this.geometry();this.attribute(f,"position",new Float32Array(tissue.fibres),3);
      this.tissueLines=new THREE.LineSegments(f,this.material({vertexShader:FIBRE_VERTEX,fragmentShader:FIBRE_FRAGMENT}));
      this.scene.add(this.tissueLines);
    }
    buildFixed() {
      this.nodes.set("@self",{id:"@self",kind:"self",title:this.labels.self||"Self",p:[0,0.08,0],color:SELF_COLOR,size:116,flare:-100});
      for(const [key,p] of Object.entries(SOURCE_AT)) this.nodes.set("~"+key,{id:"~"+key,kind:"source",source:key,
        title:this.labels.sources?.[key]||key,p,color:SOURCE_COLOR[key],size:26,flare:-100});
    }
    buildLabels() {
      this.labelLayer.replaceChildren();this.labelsDOM=[];
      for(const node of this.nodes.values()) if(["source","self","memory"].includes(node.kind)) {
        const el=document.createElement("span");
        el.className="brain-node-label"+(node.kind==="self"?" brain-core-label":node.kind==="memory"?" brain-memory-label":"");
        el.dataset.brainId=node.id;
        const text=document.createElement("span");text.className="brain-label-text";
        text.textContent=node.kind==="self"?(this.labels.core||"Core")+" · "+node.title:node.title;
        el.appendChild(text);el.title=node.title;
        el.style.setProperty("--node-color","rgb("+node.color.map(v=>Math.round(v*255)).join(",")+")");
        const leader=document.createElement("span");leader.className="brain-label-leader";leader.hidden=true;
        leader.style.setProperty("--node-color","rgb("+node.color.map(v=>Math.round(v*255)).join(",")+")");
        this.labelLayer.append(leader,el);this.labelsDOM.push({node,el,leader});
      }
    }
    memoryPosition(memory,hub) {
      const rng=random(hash(memory.id)),points=this.tissue.pts;
      const vertex=points[hub.anchor],cell=this.tissue.cell,near=[];
      const gx=Math.floor(vertex[0]/cell),gy=Math.floor(vertex[1]/cell),gz=Math.floor(vertex[2]/cell);
      for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++){
        const candidates=this.tissue.grid.get(`${gx+x},${gy+y},${gz+z}`);
        if(candidates)for(const index of candidates)if(points[index][0]*vertex[0]>=0)near.push(index);
      }
      const chosen=points[near.length?near[Math.floor(rng()*near.length)]:hub.anchor];
      // Use the actual cortex rather than an ever-expanding random cloud.
      // The deterministic inward displacement keeps a memory inside its region
      // regardless of total memory count or the order in which it was loaded.
      const depth=.79+rng()*.12;
      return chosen.map((v,i)=>v*depth+(rng()-.5)*.018*(i===0?.5:1));
    }
    setMemories(memories) {
      if(!this.running)return;
      const keep=new Set(["@self",...Object.keys(SOURCE_AT).map(k=>"~"+k)]);
      const groups=new Map();
      for(const m of memories||[]){const name=m.compartment||"memories";groups.set(name,(groups.get(name)||0)+1);}
      for(const [name,count] of groups){
        const id="#"+name;keep.add(id);let hub=this.nodes.get(id);
        if(!hub){
          const anchor=hash(name)%this.tissue.pts.length;
          hub={id,kind:"compartment",title:name,anchor,p:this.tissue.pts[anchor].map(v=>v*.84),
            color:PALETTE[hash(name)%PALETTE.length],size:10,flare:-100};this.nodes.set(id,hub);
        }
        hub.count=count;
      }
      for(const memory of memories||[]){
        if(!memory.id)continue;keep.add(memory.id);
        const hub=this.nodes.get("#"+(memory.compartment||"memories"));let node=this.nodes.get(memory.id);
        if(!node){node={id:memory.id,kind:"memory",p:this.memoryPosition(memory,hub),flare:-100};this.nodes.set(memory.id,node);}
        node.title=memory.title||memory.id;node.hub=hub.id;node.color=hub.color;
        node.strength=clamp(Number(memory.strength),0,1);node.size=26+node.strength*12;
        node.data=memory;
      }
      for(const id of this.nodes.keys())if(!keep.has(id))this.nodes.delete(id);
      this.edges=[];const seen=new Set();
      for(const key of Object.keys(SOURCE_AT))this.edges.push({from:"~"+key,to:"@self",kind:"source"});
      for(const node of this.nodes.values())if(node.kind==="memory"){
        this.edges.push({from:node.hub,to:node.id,kind:"group"});
        for(const other of node.data.links||[]){
          const key=[node.id,other].sort().join("\u0000");
          if(other!==node.id&&this.nodes.get(other)?.kind==="memory"&&!seen.has(key)){
            seen.add(key);this.edges.push({from:node.id,to:other,kind:"memory"});
          }
        }
      }
      this.counts={memories:(memories||[]).length,links:seen.size};this.memoryLoaded=true;this.rebuildNodes();
      if(this.labelLayer)this.buildLabels();
      const pending=this.pending;this.pending=[];
      for(const item of pending)if(this.time-item.at<12){
        this.pendingReplayAt=item.at;
        this[item.method](...item.args,true);
      }
      this.pendingReplayAt=undefined;
    }
    rebuildNodes() {
      const THREE=this.THREE;
      if(this.nodePoints){this.scene.remove(this.nodePoints);this.resources.delete(this.nodePoints.geometry);this.nodePoints.geometry.dispose();}
      if(this.graphLines){this.scene.remove(this.graphLines);this.resources.delete(this.graphLines.geometry);this.graphLines.geometry.dispose();}
      const order={compartment:0,source:1,memory:2,self:3};
      this.nodeList=[...this.nodes.values()].sort((a,b)=>order[a.kind]-order[b.kind]);const n=this.nodeList.length,g=this.geometry();
      const positions=new Float32Array(n*3),colors=new Float32Array(n*3),sizes=new Float32Array(n),energy=new Float32Array(n),kinds=new Float32Array(n);
      this.nodeList.forEach((node,i)=>{positions.set(node.p,i*3);colors.set(node.color,i*3);sizes[i]=node.size;node.index=i;kinds[i]=node.kind==="self"?2:node.kind==="source"?1:node.kind==="memory"?0:3;});
      this.attribute(g,"position",positions,3);this.attribute(g,"aColor",colors,3);this.attribute(g,"aSize",sizes,1);
      this.attribute(g,"aEnergy",energy,1);this.attribute(g,"aKind",kinds,1);g.attributes.aEnergy.setUsage(THREE.DynamicDrawUsage);g.computeBoundingSphere();
      if(!this.nodeMaterial)this.nodeMaterial=this.material({vertexShader:NODE_VERTEX,fragmentShader:NODE_FRAGMENT,blending:THREE.NormalBlending});
      this.nodePoints=new THREE.Points(g,this.nodeMaterial);this.nodePoints.renderOrder=6;this.nodePoints.frustumCulled=false;this.scene.add(this.nodePoints);
      const vertices=[],lineColors=[];
      for(const edge of this.edges){
        const a=this.nodes.get(edge.from),b=this.nodes.get(edge.to);if(!a||!b)continue;
        const path=curve(a.p,b.p,hash(edge.from+edge.to)),u=[0,0,0],v=[0,0,0];
        const opacity=edge.kind==="memory"?.85:edge.kind==="group"?.12:.17;
        const color=b.color.map(c=>c*opacity);bezier(...path,0,u);
        for(let i=1;i<=10;i++){
          bezier(...path,i/10,v);vertices.push(...u,...v);lineColors.push(...color,...color);u[0]=v[0];u[1]=v[1];u[2]=v[2];
        }
      }
      const lines=this.geometry();this.attribute(lines,"position",new Float32Array(vertices),3);this.attribute(lines,"color",new Float32Array(lineColors),3);
      if(!this.graphMaterial){this.graphMaterial=new THREE.LineBasicMaterial({vertexColors:true,transparent:true,opacity:.82,depthWrite:false,
        blending:THREE.AdditiveBlending});this.resources.add(this.graphMaterial);}
      this.graphLines=new THREE.LineSegments(lines,this.graphMaterial);this.graphLines.renderOrder=1;this.scene.add(this.graphLines);
    }
    buildSignalPool() {
      const THREE=this.THREE,g=this.geometry(),n=MAX_SIGNALS*TAIL;
      this.signalPosition=new Float32Array(n*3);this.signalColor=new Float32Array(n*3);this.signalSize=new Float32Array(n);
      this.signalEnergy=new Float32Array(n);this.signalPosition.fill(1000);
      this.attribute(g,"position",this.signalPosition,3);this.attribute(g,"aColor",this.signalColor,3);
      this.attribute(g,"aSize",this.signalSize,1);this.attribute(g,"aEnergy",this.signalEnergy,1);
      this.attribute(g,"aKind",new Float32Array(n).fill(4),1);
      for(const a of Object.values(g.attributes))a.setUsage(THREE.DynamicDrawUsage);
      this.signalPoints=new THREE.Points(g,this.material({vertexShader:NODE_VERTEX,fragmentShader:NODE_FRAGMENT}));
      this.signalPoints.renderOrder=4;this.signalPoints.frustumCulled=false;this.scene.add(this.signalPoints);
    }
    addWave(origin,color,amp=1,radius=2,speed=.85) {
      if(this.userControls.paused||this.contextLost||document.hidden)return;
      this.waves.push({origin:origin.slice(),color,amp:clamp(amp,0,2),radius,speed,at:this.time});
      if(this.waves.length>MAX_WAVES)this.waves.shift();
    }
    signal(from,to,color,energy=1,seconds=1.15,reach=1,delay=0) {
      const a=this.nodes.get(from),b=this.nodes.get(to);if(!a||!b||this.userControls.paused||document.hidden)return;
      const path=curve(a.p,b.p,hash(from+to));
      this.signals[this.nextSignal]={path,color,energy,seconds,reach,start:this.time+delay};
      this.nextSignal=(this.nextSignal+1)%MAX_SIGNALS;
    }
    flare(id,amount=1){
      if(this.userControls.paused||document.hidden)return;
      const node=this.nodes.get(id);if(node){node.flare=this.time;node.flareAmount=amount;}
    }
    waitFor(method,args,retry){
      // A response already in flight can predate the event's new memory. Keep
      // unresolved IDs until a later snapshot, preserving the original expiry.
      const at=retry?(this.pendingReplayAt??this.time):this.time;
      if(this.time-at>=12)return;
      this.pending.push({method,args,at});if(this.pending.length>60)this.pending.shift();
    }
    stage(source,below,salience,data) {
      const key=sourceKey(source),color=SOURCE_COLOR[key],strength=clamp(Number(salience)||.7,.15,1.4);
      this.flare("~"+key,strength);this.flare("@self",.5);
      this.addWave(SOURCE_AT[key],color,.8+strength*.5,2.1,.95);
      for(let i=0;i<4;i++)this.signal("~"+key,"@self",color,strength,1.10,1,i*.07);
      for(const [i,item]of(below||[]).slice(0,6).entries()){
        const k=sourceKey(item.source),level=clamp(Number(item.salience)||.25,.1,.5);
        this.flare("~"+k,level);this.signal("~"+k,"@self",SOURCE_COLOR[k],level,1.2,.48,i*.035);
      }
      this.lastEvent={type:"stage",source:key,...data};
    }
    recall(id,path,data,retry=false) {
      const node=this.nodes.get(id);if(!node)return this.waitFor("recall",[id,path,data],retry);
      if (typeof data?.strength === "number") {
        node.strength=clamp(data.strength,0,1);node.size=26+node.strength*12;
        node.data.strength=node.strength;
        this.nodePoints.geometry.attributes.aSize.array[node.index]=node.size;
        this.nodePoints.geometry.attributes.aSize.needsUpdate=true;
      }
      if (data?.state) node.data.state=data.state;
      const color=path==="chance"?SOURCE_COLOR.dream:path==="neighbourhood"?SOURCE_COLOR.association:SOURCE_COLOR.reminiscence;
      this.flare(id,1.4);this.flare(node.hub,.6);this.addWave(node.p,color,1.5,1.25,.8);
      for(let i=0;i<4;i++)this.signal(id,"@self",color,1.25,1.25,1,i*.09);
    }
    remember(id,data,retry=false) {
      const node=this.nodes.get(id);if(!node)return this.waitFor("remember",[id,data],retry);
      this.flare(id,1.5);this.flare(node.hub,1);this.addWave(node.p,node.color,1.6,1.0,.65);
      for(let i=0;i<5;i++)this.signal("@self",id,node.color,1.2,1.4,1,i*.08);
    }
    decision(accepted,data) {
      const color=accepted?SELF_COLOR:[1,.29,.37];this.flare("@self",accepted?1.5:.9);
      this.addWave(this.nodes.get("@self").p,color,accepted?1.35:.65,accepted?2.5:.8,1.25);
      this.lastEvent={type:"decision",accepted,...data};
    }
    speech(data) {
      this.flare("~message",1.4);this.addWave(SOURCE_AT.message,SOURCE_COLOR.message,1.2,1.2,1.3);
      for(let i=0;i<5;i++)this.signal("@self","~message",SOURCE_COLOR.message,1.25,.85,1,i*.07);
      this.lastEvent={type:"speech",...data};
    }
    read(data) {
      this.flare("~reading",1);this.addWave(SOURCE_AT.reading,SOURCE_COLOR.reading,1.2,1.3,.8);
      for(let i=0;i<3;i++)this.signal("~reading","@self",SOURCE_COLOR.reading,1.1,1.2,1,i*.09);
      this.lastEvent={type:"read",...data};
    }
    dream(ids,data,retry=false) {
      const known=(ids||[]).filter(id=>this.nodes.has(id));
      if(known.length<(ids||[]).length){this.waitFor("dream",[ids,data],retry);return;}
      this.flare("~dream",1.5);this.addWave(SOURCE_AT.dream,SOURCE_COLOR.dream,1.25,2.6,.55);
      for(const [i,id]of known.slice(0,20).entries()){
        const node=this.nodes.get(id);this.flare(id,1.4);this.addWave(node.p,SOURCE_COLOR.dream,.9,.8,.6);
        this.signal(id,"~dream",SOURCE_COLOR.dream,1.1,2,1,i*.08);
        // Dream co-activation travels to the dream source. A synapse between
        // memories is illuminated only when it is a declared persisted link.
        for (const other of (node.data?.links || []).filter(link => known.includes(link)).slice(0,8)) {
          this.signal(id,other,SOURCE_COLOR.dream,1.1,2.2,1,.12);
        }
      }
      this.lastEvent={type:"dream",...data};
    }
    setAsleep(value){this.asleep=!!value;}
    setNeeds(needs) {
      this.need=clamp(Math.max(0,...Object.entries(needs||{}).filter(([k])=>k!=="fatigue").map(([,v])=>Number(v)||0)),0,1);
      this.fatigue=clamp(Number(needs?.fatigue)||0,0,1);
    }
    setSnapshot(snapshot) {
      this.snapshot=snapshot||{};this.setNeeds(this.snapshot.needs);
      if(typeof this.snapshot.sleeping==="boolean")this.setAsleep(this.snapshot.sleeping);
    }
    setPaused(reason){this.pausedReason=reason||"";}
    setControls(settings){Object.assign(this.userControls,settings);this.last=now();}
    resetView(){this.controls.reset();this.last=now();}
    setTheme() {
      this.dark=document.documentElement.dataset.theme!=="light";
      const THREE=this.THREE;
      this.uniforms.uBaseColor.value.copy(new THREE.Color(...(this.dark?[.08,.44,.61]:[.05,.31,.48])));
      this.uniforms.uAmbient.value=this.dark?.24:.20;
      this.uniforms.uLineOpacity.value=this.dark?.045:.075;
      this.uniforms.uNodeOpacity.value=1;this.uniforms.uLightTheme.value=this.dark?0:1;
      for(const object of [this.tissuePoints,this.tissueLines,this.signalPoints]){
        object.material.blending=this.dark?THREE.AdditiveBlending:THREE.NormalBlending;object.material.needsUpdate=true;
      }
      this.graphMaterial.blending=this.dark?THREE.AdditiveBlending:THREE.NormalBlending;this.graphMaterial.needsUpdate=true;
    }
    info(node) {
      const data={kind:node.kind,id:node.id,title:node.title};
      if(node.source)data.source=node.source;
      if(node.kind==="memory")Object.assign(data,{strength:node.strength,links:node.data.links||[],compartment:node.data.compartment,
        summary:node.data.summary,state:node.data.state});
      if(node.kind==="compartment")data.count=node.count;
      return data;
    }
    layoutLabels() {
      const occupied=[], pad=8;
      const items=this.labelsDOM.map(item=>{
        this.projection.set(...item.node.p).project(this.camera);
        return {...item,x:(this.projection.x*.5+.5)*this.w,y:(-this.projection.y*.5+.5)*this.h,z:this.projection.z};
      });
      const overlaps=rect=>occupied.some(b=>rect.x<b.x+b.w+pad&&rect.x+rect.w+pad>b.x&&rect.y<b.y+b.h+pad&&rect.y+rect.h+pad>b.y);
      const fits=rect=>rect.x>16&&rect.x+rect.w<this.w-16&&rect.y>115&&rect.y+rect.h<this.h-48
        &&!(rect.x+rect.w>this.w-320&&rect.y+rect.h>this.h-300)
        &&!(rect.x<340&&rect.y+rect.h>this.h-130);
      const show=(item,rect)=>{
        item.el.hidden=false;item.el.style.transform=`translate(${Math.round(rect.x)}px,${Math.round(rect.y)}px)`;
        item.el.classList.toggle("is-active",this.hover===item.node||this.time-item.node.flare<1.8);
        occupied.push(rect);
        const tx=clamp(item.x,rect.x,rect.x+rect.w),ty=clamp(item.y,rect.y,rect.y+rect.h);
        const length=Math.hypot(tx-item.x,ty-item.y);
        item.leader.hidden=length<5;
        if(length>=5){item.leader.style.left=item.x+"px";item.leader.style.top=item.y+"px";
          item.leader.style.width=length+"px";item.leader.style.transform=`rotate(${Math.atan2(ty-item.y,tx-item.x)}rad)`;}
      };
      for(const item of items){item.el.hidden=true;item.leader.hidden=true;}
      const core=items.find(item=>item.node.kind==="self");
      if(core&&core.z<1){
        // Leave the central orb and its rings free of title collisions.
        occupied.push({x:core.x-65,y:core.y-65,w:130,h:130});
        show(core,{x:clamp(core.x-78,16,this.w-172),y:core.y+62,w:156,h:30});
      }
      const memories=items.filter(item=>item.node.kind==="memory"&&item.z<1&&item.z>-1);
      memories.sort((a,b)=>{
        const priority=item=>(this.hover===item.node?100:0)+Math.max(0,1.8-(this.time-item.node.flare))*12+(item.node.strength||0);
        return priority(b)-priority(a)||a.node.id.localeCompare(b.node.id);
      });
      let shown=0;
      for(const item of memories){
        if(shown>=7&&this.hover!==item.node)continue;
        const width=Math.min(178,Math.max(90,item.node.title.length*6.1+30)),height=28;
        const offsets=[[18,-36],[-width-18,-36],[18,14],[-width-18,14],[24,-74],[-width-24,-74],[28,48],[-width-28,48],[40,-112],[-width-40,-112]];
        for(const [dx,dy]of offsets){const rect={x:item.x+dx,y:item.y+dy,w:width,h:height};
          if(fits(rect)&&!overlaps(rect)){show(item,rect);shown++;break;}}
      }
      // Source titles are secondary to the core and actual memories.
      for(const item of items.filter(item=>item.node.kind==="source"&&item.z<1)){
        const width=Math.min(145,Math.max(75,item.node.title.length*6.0+25));
        for(const [dx,dy]of [[14,-18],[-width-14,-18],[14,22],[-width-14,22]]){
          const rect={x:item.x+dx,y:item.y+dy,w:width,h:25};
          if(fits(rect)&&!overlaps(rect)){show(item,rect);break;}
        }
      }
    }
    resize() {
      if(!this.running)return;
      const box=this.canvas.getBoundingClientRect();this.w=Math.max(1,box.width);this.h=Math.max(1,box.height);
      this.renderer.setSize(this.w,this.h,false);this.camera.aspect=this.w/this.h;this.camera.updateProjectionMatrix();
    }
    pick(event) {
      if(!this.running||this.contextLost||this.down&&Math.hypot(event.clientX-this.down.x,event.clientY-this.down.y)>5)return;
      const box=this.canvas.getBoundingClientRect();
      this.pointer.set((event.clientX-box.left)/box.width*2-1,-(event.clientY-box.top)/box.height*2+1);
      this.raycaster.setFromCamera(this.pointer,this.camera);
      const hits=this.raycaster.intersectObject(this.nodePoints,false);
      const hit=hits.find(item=>this.nodeList[item.index]);this.hover=hit?this.nodeList[hit.index]:null;
      this.canvas.style.cursor=this.hover?"pointer":"grab";this.tip.hidden=!this.hover;
      if(this.hover){this.tip.textContent=this.hover.title;
        this.tip.style.left=clamp(event.clientX-box.left+14,8,this.w-240)+"px";
        this.tip.style.top=clamp(event.clientY-box.top+14,8,this.h-70)+"px";}
    }
    updateSignals() {
      const p=[0,0,0],motion=this.userControls.motion&&!this.reduced;
      for(let i=0;i<MAX_SIGNALS;i++){
        const signal=this.signals[i];
        if(!signal){for(let tail=0;tail<TAIL;tail++)this.signalSize[i*TAIL+tail]=0;continue;}
        const elapsed=(this.time-signal.start)/signal.seconds;
        if(elapsed>1.3){this.signals[i]=null;for(let tail=0;tail<TAIL;tail++)this.signalSize[i*TAIL+tail]=0;continue;}
        for(let tail=0;tail<TAIL;tail++){
          const index=i*TAIL+tail,t=elapsed-tail*.025;
          if(t<0||t>1||!motion){this.signalSize[index]=0;continue;}
          bezier(...signal.path,t*signal.reach,p);this.signalPosition.set(p,index*3);this.signalColor.set(signal.color,index*3);
          this.signalSize[index]=(13-tail*.9)*signal.energy*(1-tail/TAIL);
          this.signalEnergy[index]=Math.min(1,signal.energy)*(1-tail/TAIL)*(signal.reach<1?1-t:1);
        }
      }
      for(const attribute of Object.values(this.signalPoints.geometry.attributes))attribute.needsUpdate=true;
    }
    frame(timestamp) {
      if(!this.running)return;
      this.raf=requestAnimationFrame(this.frame);
      const elapsed=Math.max(0,(timestamp-this.last)/1000),dt=Math.min(.05,elapsed);this.last=timestamp;
      if(document.hidden||this.contextLost)return;
      const paused=this.userControls.paused;
      // Preserve real durations on software-rendered or busy devices. A paused
      // life stops new events; its final real effects must still dissipate.
      if(!paused)this.time+=elapsed;
      const motion=this.userControls.motion&&!this.reduced;
      this.controls.autoRotate=!!(this.userControls.rotate&&motion&&!paused&&!this.pausedReason);
      this.controls.autoRotateSpeed=this.asleep?.04:.18;
      this.controls.update(dt);
      this.uniforms.uTime.value=this.time;
      // Needs change a continuous state light; they never fabricate events.
      this.waves=this.waves.filter(w=>(this.time-w.at)*w.speed<w.radius+.3);
      for(let i=0;i<MAX_WAVES;i++){
        const wave=motion?this.waves[i]:null;
        if(wave){this.uniforms.uWaveOrigin.value[i].set(...wave.origin,wave.at);
          this.uniforms.uWaveColor.value[i].set(...wave.color,wave.amp);
          this.uniforms.uWaveShape.value[i].set(wave.speed,wave.radius);}
        else this.uniforms.uWaveOrigin.value[i].w=-1000;
      }
      const energies=this.nodePoints.geometry.attributes.aEnergy.array;
      for(const node of this.nodeList){
        let level=Math.max(0,1-(this.time-node.flare)/1.8)*(node.flareAmount||1);
        if(node.source==="need")level+=this.need*.18;
        if(node.kind==="self")level+=this.asleep?.04:.12;
        energies[node.index]=clamp(level,0,2);
      }
      this.nodePoints.geometry.attributes.aEnergy.needsUpdate=true;
      this.updateSignals();
      this.layoutLabels();
      this.renderer.render(this.scene,this.camera);
    }
    destroy() {
      if(!this.running)return;this.running=false;cancelAnimationFrame(this.raf);
      this.resizeObserver.disconnect();this.controls.dispose();this.labelLayer.remove();this.tip.hidden=true;
      const c=this.canvas;c.removeEventListener("pointermove",this.onMove);c.removeEventListener("pointerdown",this.onDown);
      c.removeEventListener("pointerup",this.onUp);c.removeEventListener("pointerleave",this.onLeave);
      c.removeEventListener("webglcontextlost",this.onLost);c.removeEventListener("webglcontextrestored",this.onRestored);
      document.removeEventListener("visibilitychange",this.onVisibility);this.media.removeEventListener("change",this.onMedia);
      for(const resource of this.resources)resource.dispose();this.resources.clear();
      this.renderer.dispose();this.scene.clear();this.nodes.clear();this.pending=[];this.signals=[];
    }
  }
  window.Brain=Brain;
})();
