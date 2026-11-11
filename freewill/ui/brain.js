// The Brain view: an instrument of observation.
//
// What is real: the self at the centre, the sources of the subconscious around
// it, every memory (grouped by the compartments the being chose), the links
// between memories, and every wave and pulse of light, each of which is fired
// by one event of the being's life at the moment it happens. What is not: the
// faint mesh in the shape of a brain. It is only the tissue the waves travel
// through, and the legend says so.
(function () {
  "use strict";

  const SOURCE_COLOR = {
    message: [79, 195, 247], reminiscence: [255, 182, 92], need: [255, 123, 156], question: [197, 139, 255],
    association: [95, 214, 163], drift: [150, 160, 200], reading: [127, 212, 201], dream: [176, 124, 255],
  };
  // Where each source of the subconscious sits, in brain space (x: right, y: up, z: front).
  const NUCLEUS_AT = {
    message: [0, 0.02, 0.62], question: [0, 0.4, 0.26], association: [0.44, 0.18, -0.16],
    reminiscence: [-0.46, -0.1, 0.1], need: [0, -0.36, 0.02], drift: [0.3, -0.24, -0.52],
    reading: [-0.4, 0.24, -0.42], dream: [0, 0.1, -0.74],
  };
  const PALETTE = [[124, 116, 255], [255, 143, 177], [79, 195, 247], [255, 182, 92], [95, 214, 163],
                   [197, 139, 255], [255, 123, 123], [127, 212, 201]];
  const SELF = [170, 164, 255];
  const TISSUE = 2100;

  function mulberry(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hash(text) {
    let h = 2166136261;
    for (let i = 0; i < text.length; i++) { h ^= text.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function sourceKey(source) {
    if (!source) return "drift";
    if (source.startsWith("need")) return "need";
    if (source === "return") return "message";
    return NUCLEUS_AT[source] ? source : "drift";
  }
  const rgba = (c, a) => "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + a + ")";

  // The tissue: two hemispheres and a cerebellum, as a shell of points.
  function buildTissue() {
    const rand = mulberry(20261111), pts = [];
    function lobe(count, cx, cy, cz, rx, ry, rz) {
      let made = 0;
      while (made < count) {
        const u = rand() * 2 - 1, phi = rand() * Math.PI * 2, s = Math.sqrt(1 - u * u);
        let x = s * Math.cos(phi), y = u, z = s * Math.sin(phi);
        // Folds: the surface ripples, and a few points sit deeper, like white matter.
        const fold = 1 + 0.06 * Math.sin(9 * x + 4 * z) * Math.cos(7 * y + 3 * x);
        const depth = rand() < 0.22 ? 0.45 + 0.4 * rand() : 0.9 + 0.1 * rand();
        x = cx + x * rx * fold * depth; y = cy + y * ry * fold * depth; z = cz + z * rz * fold * depth;
        // Flatten the inner face of each hemisphere to leave the fissure between them.
        if (cx !== 0 && Math.sign(cx) * x < 0.035) continue;
        pts.push([x, y, z]); made++;
      }
    }
    lobe(920, -0.36, 0.06, 0.02, 0.5, 0.56, 0.98);
    lobe(920, 0.36, 0.06, 0.02, 0.5, 0.56, 0.98);
    lobe(TISSUE - 1840, 0, -0.5, -0.72, 0.5, 0.26, 0.34);
    // Each point reaches for its two nearest neighbours.
    const edges = [];
    for (let i = 0; i < pts.length; i++) {
      let a = -1, b = -1, da = 1e9, db = 1e9;
      for (let j = 0; j < pts.length; j++) {
        if (i === j) continue;
        const dx = pts[i][0] - pts[j][0], dy = pts[i][1] - pts[j][1], dz = pts[i][2] - pts[j][2];
        const d = dx * dx + dy * dy + dz * dz;
        if (d < da) { b = a; db = da; a = j; da = d; } else if (d < db) { b = j; db = d; }
      }
      if (a > i || da > 0) edges.push(i, a);
      if (b >= 0) edges.push(i, b);
    }
    return { pts, edges };
  }
  let TISSUE_CACHE = null;

  class Brain {
    constructor(canvas, tip, labels, options) {
      this.canvas = canvas; this.tip = tip; this.labels = labels; this.options = options || {};
      this.ctx = canvas.getContext("2d");
      this.tissue = TISSUE_CACHE || (TISSUE_CACHE = buildTissue());
      const n = this.tissue.pts.length;
      this.sx = new Float32Array(n); this.sy = new Float32Array(n); this.sz = new Float32Array(n);
      this.act = new Float32Array(n); this.acol = new Float32Array(n * 3);
      this.nodes = new Map(); this.links = []; this.waves = []; this.pulses = []; this.rings = [];
      this.sprites = new Map();
      this.yaw = 0.6; this.pitch = 0.2; this.zoom = 1; this.spin = 0; this.asleep = false; this.sleepMix = 0;
      this.drag = null; this.hover = null; this.running = true; this.last = performance.now();
      this.still = matchMedia("(prefers-reduced-motion: reduce)").matches;
      this.buildFixed();

      this.onDown = (e) => { this.drag = { x: e.clientX, y: e.clientY, moved: 0 }; canvas.setPointerCapture(e.pointerId); };
      this.onMove = (e) => {
        if (this.drag) {
          const dx = e.clientX - this.drag.x, dy = e.clientY - this.drag.y;
          this.drag.moved += Math.abs(dx) + Math.abs(dy);
          this.yaw += dx * 0.006; this.pitch = Math.max(-1.1, Math.min(1.1, this.pitch + dy * 0.005));
          this.drag.x = e.clientX; this.drag.y = e.clientY; this.tip.hidden = true;
        } else this.pick(e);
      };
      this.onUp = (e) => {
        const was = this.drag; this.drag = null;
        if (was && was.moved < 5 && this.hover && this.hover.kind === "memory" && this.options.onOpen) this.options.onOpen(this.hover.id);
      };
      this.onLeave = () => { this.hover = null; this.tip.hidden = true; };
      this.onWheel = (e) => { e.preventDefault(); this.zoom = Math.max(0.6, Math.min(2.4, this.zoom * Math.exp(-e.deltaY * 0.0012))); };
      canvas.addEventListener("pointerdown", this.onDown);
      canvas.addEventListener("pointermove", this.onMove);
      canvas.addEventListener("pointerup", this.onUp);
      canvas.addEventListener("pointerleave", this.onLeave);
      canvas.addEventListener("wheel", this.onWheel, { passive: false });
      this.observer = new ResizeObserver(() => this.resize());
      this.observer.observe(canvas);
      this.resize();
      requestAnimationFrame((t) => this.frame(t));
    }

    destroy() {
      this.running = false; this.observer.disconnect();
      const c = this.canvas;
      c.removeEventListener("pointerdown", this.onDown); c.removeEventListener("pointermove", this.onMove);
      c.removeEventListener("pointerup", this.onUp); c.removeEventListener("pointerleave", this.onLeave);
      c.removeEventListener("wheel", this.onWheel);
    }

    resize() {
      const ratio = Math.min(2, window.devicePixelRatio || 1), box = this.canvas.getBoundingClientRect();
      this.w = box.width; this.h = box.height;
      this.canvas.width = Math.max(1, Math.round(box.width * ratio));
      this.canvas.height = Math.max(1, Math.round(box.height * ratio));
      this.ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    }

    // ----- what is real -----

    buildFixed() {
      this.nodes.set("@self", { id: "@self", kind: "self", title: this.labels.self, p: [0, 0, 0], color: SELF, r: 11 });
      for (const [key, p] of Object.entries(NUCLEUS_AT)) {
        this.nodes.set("~" + key, { id: "~" + key, kind: "nucleus", title: (this.labels.sources || {})[key] || key,
                                    p, color: SOURCE_COLOR[key], r: 5.2 });
      }
    }

    // memories: [{id, title, compartment, strength, links}]
    setMemories(memories) {
      const now = performance.now(), first = !this.loaded;
      const keep = new Set(["@self", ...Object.keys(NUCLEUS_AT).map((k) => "~" + k)]);
      const compartments = [...new Set(memories.map((m) => m.compartment))].sort();
      compartments.forEach((name, i) => {
        const id = "#" + name; keep.add(id);
        if (!this.nodes.has(id)) {
          // A compartment settles on the cortex, at a place set by its name.
          const h = hash(name), u = ((h & 0xffff) / 0xffff) * 1.5 - 0.6, phi = ((h >>> 16) / 0xffff) * Math.PI * 2;
          const s = Math.sqrt(Math.max(0, 1 - u * u));
          this.nodes.set(id, { id, kind: "hub", title: name, r: 3.4,
                               p: [s * Math.cos(phi) * 0.8, u * 0.56, s * Math.sin(phi) * 0.95] });
        }
        this.nodes.get(id).color = PALETTE[i % PALETTE.length];
      });
      memories.forEach((m) => {
        keep.add(m.id);
        const hub = this.nodes.get("#" + m.compartment);
        let node = this.nodes.get(m.id);
        if (!node) {
          const rand = mulberry(hash(m.id));
          const spread = 0.2 + 0.035 * Math.sqrt(memories.length);
          const p = [hub.p[0] + (rand() - 0.5) * spread, hub.p[1] + (rand() - 0.5) * spread, hub.p[2] + (rand() - 0.5) * spread];
          node = { id: m.id, kind: "memory", p, born: first ? 0 : now, flare: 0 };
          this.nodes.set(m.id, node);
          if (!first) { // a memory has just been kept: the self writes it into the cortex
            this.pulse("@self", m.id, hub.color, 1.1, 1.4);
            this.wave(p, hub.color, 0.7, 0.9);
          }
        }
        node.title = m.title; node.hub = hub.id; node.color = hub.color;
        node.strength = Math.max(0, Math.min(1, m.strength)); node.r = 3 + 3.6 * node.strength;
      });
      for (const id of [...this.nodes.keys()]) if (!keep.has(id)) this.nodes.delete(id);
      this.links = [];
      for (const key of Object.keys(NUCLEUS_AT)) this.links.push(["@self", "~" + key, 0.16]);
      compartments.forEach((name) => this.links.push(["@self", "#" + name, 0.1]));
      const seen = new Set();
      memories.forEach((m) => {
        this.links.push(["#" + m.compartment, m.id, 0.13]);
        (m.links || []).forEach((other) => {
          const key = m.id < other ? m.id + "|" + other : other + "|" + m.id;
          if (!this.nodes.has(other) || seen.has(key)) return;
          seen.add(key); this.links.push([m.id, other, 0.3]);
        });
      });
      this.loaded = true;
      this.counts = { memories: memories.length, links: this.links.filter((l) => l[2] === 0.3).length };
    }

    // ----- what happens -----

    wave(origin, color, amp, radius, speed) {
      this.waves.push({ o: origin, color, amp, R: radius, speed: speed || 0.9, t0: performance.now() });
      if (this.waves.length > 14) this.waves.shift();
    }
    pulse(from, to, color, size, seconds, reach) {
      if (!this.nodes.has(from) || !this.nodes.has(to)) return;
      this.pulses.push({ from, to, color, size: size || 1, dur: (seconds || 1) * 1000, reach: reach || 1,
                         t0: performance.now(), bend: (hash(from + to) % 100) / 100 - 0.5 });
    }
    ring(color, strength) { this.rings.push({ color, strength, t0: performance.now() }); }

    // A content reaches the stage; the others stay below attention.
    stage(source, below) {
      const key = sourceKey(source), color = SOURCE_COLOR[key];
      this.wave(NUCLEUS_AT[key], color, 1, 1.7);
      this.pulse("~" + key, "@self", color, 1.5, 0.9);
      const node = this.nodes.get("~" + key); if (node) node.flare = performance.now();
      (below || []).forEach((b, i) => {
        const k = sourceKey(b.source);
        setTimeout(() => {
          if (!this.running) return;
          this.wave(NUCLEUS_AT[k], SOURCE_COLOR[k], 0.34, 0.5, 0.6);
          this.pulse("~" + k, "@self", SOURCE_COLOR[k], 0.6, 1.1, 0.45); // rises, and fades before the stage
        }, 90 * i);
      });
    }
    recall(id) {
      const node = this.nodes.get(id); if (!node) return;
      node.flare = performance.now();
      this.wave(node.p, node.color, 0.5, 0.6);
      this.pulse(id, "@self", node.color, 1.1, 1.1);
    }
    decision(accepted) {
      if (accepted) { this.ring(SELF, 1); this.wave([0, 0, 0], [225, 222, 255], 0.8, 2.3, 1.25); }
      else this.ring([255, 113, 134], 0.45);
    }
    speech() { this.pulse("@self", "~message", SOURCE_COLOR.message, 1.4, 0.7); this.wave(NUCLEUS_AT.message, SOURCE_COLOR.message, 0.7, 1.2, 1.4); }
    read() { this.pulse("~reading", "@self", SOURCE_COLOR.reading, 1.2, 1); }
    dream(ids) {
      const color = SOURCE_COLOR.dream, real = (ids || []).filter((id) => this.nodes.has(id));
      real.forEach((id, i) => {
        const node = this.nodes.get(id); node.flare = performance.now();
        this.wave(node.p, color, 0.6, 0.9, 0.5);
        const next = real[(i + 1) % real.length];
        if (next !== id) this.pulse(id, next, color, 1.2, 2.2);
      });
      this.wave(NUCLEUS_AT.dream, color, 0.8, 2.2, 0.45);
    }
    setAsleep(asleep) { this.asleep = !!asleep; }
    // The being's needs are felt all the time: the most pressing one sends slow ripples.
    setNeeds(needs) {
      let level = 0;
      for (const [name, value] of Object.entries(needs || {})) if (name !== "fatigue") level = Math.max(level, value);
      this.need = Math.max(0, Math.min(1, level)); this.fatigue = Math.max(0, Math.min(1, (needs || {}).fatigue || 0));
    }

    // ----- drawing -----

    sprite(color) {
      const key = color.join(",");
      let s = this.sprites.get(key);
      if (!s) {
        s = document.createElement("canvas"); s.width = s.height = 64;
        const g = s.getContext("2d"), grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
        grad.addColorStop(0, rgba(color, 1)); grad.addColorStop(0.25, rgba(color, 0.55));
        grad.addColorStop(0.6, rgba(color, 0.12)); grad.addColorStop(1, rgba(color, 0));
        g.fillStyle = grad; g.fillRect(0, 0, 64, 64);
        this.sprites.set(key, s);
      }
      return s;
    }
    glow(x, y, radius, color, alpha) {
      if (alpha <= 0.003 || radius <= 0) return;
      this.ctx.globalAlpha = Math.min(1, alpha);
      this.ctx.drawImage(this.sprite(color), x - radius, y - radius, radius * 2, radius * 2);
    }

    project(p, out) {
      const x = p[0] * this.cy_ - p[2] * this.sy_, z0 = p[0] * this.sy_ + p[2] * this.cy_;
      const y = p[1] * this.cp_ - z0 * this.sp_, z = p[1] * this.sp_ + z0 * this.cp_;
      const k = 3.4 / (3.4 - z);
      out.x = this.cx + x * this.scale * k; out.y = this.cyc - y * this.scale * k; out.z = z; out.k = k;
      return out;
    }

    pick(event) {
      const box = this.canvas.getBoundingClientRect(), mx = event.clientX - box.left, my = event.clientY - box.top;
      let best = null, bestD = 16 * 16;
      this.nodes.forEach((node) => {
        if (node.sx == null) return;
        const d = (node.sx - mx) ** 2 + (node.sy - my) ** 2;
        if (d < bestD) { best = node; bestD = d; }
      });
      this.hover = best;
      this.canvas.style.cursor = best && best.kind === "memory" ? "pointer" : "grab";
      if (!best) { this.tip.hidden = true; return; }
      this.tip.hidden = false; this.tip.textContent = best.title;
      this.tip.style.left = Math.min(this.w - 290, mx + 14) + "px"; this.tip.style.top = my + 14 + "px";
    }

    frame(now) {
      if (!this.running) return;
      const dt = Math.min(0.05, (now - this.last) / 1000); this.last = now;
      const ctx = this.ctx, dark = document.documentElement.dataset.theme === "dark";
      this.sleepMix += ((this.asleep ? 1 : 0) - this.sleepMix) * Math.min(1, dt * 1.5);
      if (!this.drag && !this.still) this.yaw += dt * (0.11 - 0.07 * this.sleepMix);
      this.cy_ = Math.cos(this.yaw); this.sy_ = Math.sin(this.yaw); this.cp_ = Math.cos(this.pitch); this.sp_ = Math.sin(this.pitch);
      this.cx = this.w / 2; this.cyc = this.h / 2 - 8; this.scale = Math.min(this.w * 0.62, this.h) * 0.47 * this.zoom;
      if (!this.asleep && this.need > 0.05 && now - (this.lastNeed || 0) > 2600 - 1200 * this.need) {
        this.lastNeed = now;
        this.wave(NUCLEUS_AT.need, SOURCE_COLOR.need, 0.12 + 0.3 * this.need, 0.5 + 0.5 * this.need, 0.45);
      }

      ctx.globalCompositeOperation = "source-over"; ctx.globalAlpha = 1;
      ctx.clearRect(0, 0, this.w, this.h);
      ctx.globalCompositeOperation = dark ? "lighter" : "source-over";
      const ink = dark ? [140, 150, 235] : [70, 76, 130];
      const tint = (c) => (dark ? c : [Math.round(c[0] * 0.72), Math.round(c[1] * 0.72), Math.round(c[2] * 0.78)]);
      const boost = dark ? 1 : 1.35;

      // Waves of activity through the tissue.
      this.waves = this.waves.filter((w) => (now - w.t0) / 1000 * w.speed < w.R + 0.3);
      const pts = this.tissue.pts, act = this.act, acol = this.acol, o = { x: 0, y: 0, z: 0, k: 1 };
      act.fill(0); acol.fill(0);
      for (const w of this.waves) {
        const front = (now - w.t0) / 1000 * w.speed, c = tint(w.color);
        for (let i = 0; i < pts.length; i++) {
          const p = pts[i], dx = p[0] - w.o[0], dy = p[1] - w.o[1], dz = p[2] - w.o[2];
          const d = Math.sqrt(dx * dx + dy * dy + dz * dz);
          if (d > w.R) continue;
          const off = (d - front) / 0.16;
          if (off > 2.5 || off < -4) continue;
          // A bright front, and a short afterglow behind it.
          const a = w.amp * (1 - d / w.R) * (off > 0 ? Math.exp(-off * off) : Math.exp(-off * off * 0.22));
          if (a < 0.01) continue;
          act[i] += a; acol[i * 3] += c[0] * a; acol[i * 3 + 1] += c[1] * a; acol[i * 3 + 2] += c[2] * a;
        }
      }

      // Tissue: points, then the fibres between them.
      for (let i = 0; i < pts.length; i++) { this.project(pts[i], o); this.sx[i] = o.x; this.sy[i] = o.y; this.sz[i] = o.z; }
      const breath = 0.5 + 0.5 * Math.sin(now / (1400 + 1800 * this.sleepMix));
      const edges = this.tissue.edges;
      ctx.lineWidth = 0.6; ctx.strokeStyle = rgba(ink, dark ? 0.11 : 0.13); ctx.globalAlpha = 1;
      ctx.beginPath();
      for (let e = 0; e < edges.length; e += 2) {
        const a = edges[e], b = edges[e + 1];
        ctx.moveTo(this.sx[a], this.sy[a]); ctx.lineTo(this.sx[b], this.sy[b]);
      }
      ctx.stroke();
      for (let e = 0; e < edges.length; e += 2) {
        const a = edges[e], b = edges[e + 1], level = (act[a] + act[b]) / 2;
        if (level < 0.05) continue;
        const i = act[a] > act[b] ? a : b, s = act[i] || 1;
        ctx.strokeStyle = "rgb(" + Math.round(acol[i * 3] / s) + "," + Math.round(acol[i * 3 + 1] / s) + "," + Math.round(acol[i * 3 + 2] / s) + ")";
        ctx.globalAlpha = Math.min(1, level * 1.3 * boost); ctx.lineWidth = 0.8 + level * 1.6;
        ctx.beginPath(); ctx.moveTo(this.sx[a], this.sy[a]); ctx.lineTo(this.sx[b], this.sy[b]); ctx.stroke();
      }
      const violet = tint(SOURCE_COLOR.dream);
      for (let i = 0; i < pts.length; i++) {
        const depth = 0.45 + 0.55 * (this.sz[i] + 1.2) / 2.4, a = act[i];
        ctx.globalAlpha = Math.min(1, (0.2 + 0.5 * depth * depth) * boost);
        ctx.fillStyle = this.sleepMix > 0.5 ? rgba(violet, 1) : rgba(ink, 1);
        const size = 0.8 + 1.5 * depth * depth;
        ctx.fillRect(this.sx[i] - size / 2, this.sy[i] - size / 2, size, size);
        if (a > 0.03) {
          const c = [Math.round(acol[i * 3] / a), Math.round(acol[i * 3 + 1] / a), Math.round(acol[i * 3 + 2] / a)];
          this.glow(this.sx[i], this.sy[i], (4 + 13 * Math.min(1, a)) * depth, c, Math.min(1, a * 1.5 * boost));
        }
      }

      // Real nodes: positions first, then links, then the nodes themselves from back to front.
      const drawn = [];
      this.nodes.forEach((node) => {
        this.project(node.p, o); node.sx = o.x; node.sy = o.y; node.sz = o.z; node.sk = o.k; drawn.push(node);
      });
      for (const [a, b, alpha] of this.links) {
        const A = this.nodes.get(a), B = this.nodes.get(b); if (!A || !B) continue;
        const color = alpha === 0.3 ? tint(B.color || SELF) : ink;
        ctx.globalAlpha = Math.min(1, alpha * (dark ? 1 : 1.5) * (0.5 + 0.5 * (A.sz + B.sz + 2.4) / 4.8));
        ctx.strokeStyle = rgba(color, 1); ctx.lineWidth = alpha === 0.3 ? 1 : 0.7;
        ctx.beginPath(); ctx.moveTo(A.sx, A.sy); ctx.lineTo(B.sx, B.sy); ctx.stroke();
      }
      drawn.sort((a, b) => a.sz - b.sz);
      ctx.textAlign = "center"; ctx.font = "11.5px 'Segoe UI', system-ui, sans-serif";
      for (const node of drawn) {
        const depth = 0.5 + 0.5 * (node.sz + 1.2) / 2.4, c = tint(node.color || SELF);
        const flare = node.flare ? Math.max(0, 1 - (now - node.flare) / 1600) : 0;
        const born = node.born ? Math.max(0, 1 - (now - node.born) / 2600) : 0;
        let r = node.r * node.sk * (this.scale / 260);
        if (node.kind === "self") {
          r *= 1 + 0.12 * breath;
          this.glow(node.sx, node.sy, r * 9, c, (0.34 + 0.22 * breath) * boost);
          this.glow(node.sx, node.sy, r * 4, c, 0.8);
          this.glow(node.sx, node.sy, r * 2.2, dark ? [255, 255, 255] : c, 1);
          // Three slow orbits: fatigue slows them, sleep nearly stops them.
          ctx.lineWidth = 0.8; ctx.strokeStyle = rgba(c, 1);
          for (let k = 0; k < 3; k++) {
            const turn = now / (5200 + 5000 * (this.fatigue || 0) + 14000 * this.sleepMix) + k * 2.1;
            ctx.globalAlpha = 0.34 * boost;
            ctx.beginPath(); ctx.ellipse(node.sx, node.sy, r * (2.6 + k * 0.9), r * (0.9 + k * 0.35), turn, 0, Math.PI * 2); ctx.stroke();
          }
        } else {
          const live = Math.max(flare, born);
          this.glow(node.sx, node.sy, r * (4 + 6 * live), c, (0.62 + 0.38 * live) * (0.4 + 0.6 * depth) * boost);
          this.glow(node.sx, node.sy, r * 1.5, dark ? [255, 255, 255] : c, 0.6 * depth + 0.4 * live);
        }
        if (node.kind !== "memory" || node === this.hover) {
          ctx.globalAlpha = (node.kind === "self" ? 0.95 : 0.34 + 0.5 * depth) * (node.kind === "hub" ? 0.8 : 1);
          ctx.fillStyle = dark ? "#dfe2f2" : "#2a2e44";
          ctx.fillText(node.title, node.sx, node.sy + r * 1.6 + 13);
        }
      }

      // Pulses: light travelling from one real node to another.
      this.pulses = this.pulses.filter((p) => now - p.t0 < p.dur);
      for (const p of this.pulses) {
        const A = this.nodes.get(p.from), B = this.nodes.get(p.to); if (!A || !B || A.sx == null) continue;
        const t = (now - p.t0) / p.dur, c = tint(p.color);
        const mx = (A.sx + B.sx) / 2 - (B.sy - A.sy) * 0.22 * p.bend, my = (A.sy + B.sy) / 2 + (B.sx - A.sx) * 0.22 * p.bend;
        for (let tail = 0; tail < 9; tail++) {
          const u = (t - tail * 0.022) * p.reach; if (u < 0) break;
          const v = 1 - u, x = v * v * A.sx + 2 * v * u * mx + u * u * B.sx, y = v * v * A.sy + 2 * v * u * my + u * u * B.sy;
          const fade = (1 - tail / 9) * (p.reach < 1 ? 1 - t : Math.min(1, (1 - t) * 6));
          this.glow(x, y, (7 - tail * 0.55) * p.size * (this.scale / 260), c, 0.85 * fade * boost);
          if (tail === 0) this.glow(x, y, 2.6 * p.size * (this.scale / 260), dark ? [255, 255, 255] : c, fade);
        }
      }

      // Rings around the self: a decision has just been taken.
      const self = this.nodes.get("@self");
      this.rings = this.rings.filter((r) => now - r.t0 < 1300);
      for (const r of this.rings) {
        const t = (now - r.t0) / 1300;
        ctx.globalAlpha = (1 - t) * 0.8 * r.strength * boost; ctx.strokeStyle = rgba(tint(r.color), 1); ctx.lineWidth = 2.2 * (1 - t) + 0.4;
        ctx.beginPath(); ctx.arc(self.sx, self.sy, (10 + 150 * t * r.strength) * (this.scale / 260), 0, Math.PI * 2); ctx.stroke();
      }

      ctx.globalAlpha = 1; ctx.globalCompositeOperation = "source-over";
      requestAnimationFrame((t) => this.frame(t));
    }
  }

  window.Brain = Brain;
})();
