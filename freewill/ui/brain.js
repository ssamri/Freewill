// The Brain view: an instrument of observation, not an illustration.
// Nodes are real memories, edges are their real links, pulses are real recalls.
(function () {
  const PALETTE = ["#7c74ff", "#ff8fb1", "#4fc3f7", "#ffb65c", "#5fd6a3", "#c58bff", "#ff7b7b", "#7fd4c9"];

  class Brain {
    constructor(canvas, tip, labels) {
      this.canvas = canvas; this.tip = tip; this.labels = labels;
      this.ctx = canvas.getContext("2d");
      this.nodes = new Map(); this.edges = []; this.pulses = []; this.ripples = [];
      this.hover = null; this.running = true; this.t0 = performance.now();
      this.onMove = (e) => this.pick(e);
      this.onLeave = () => { this.hover = null; this.tip.hidden = true; };
      canvas.addEventListener("mousemove", this.onMove);
      canvas.addEventListener("mouseleave", this.onLeave);
      this.observer = new ResizeObserver(() => this.resize());
      this.observer.observe(canvas);
      this.resize();
      requestAnimationFrame((t) => this.frame(t));
    }

    destroy() {
      this.running = false; this.observer.disconnect();
      this.canvas.removeEventListener("mousemove", this.onMove);
      this.canvas.removeEventListener("mouseleave", this.onLeave);
    }

    resize() {
      const ratio = window.devicePixelRatio || 1, box = this.canvas.getBoundingClientRect();
      this.w = box.width; this.h = box.height;
      this.canvas.width = Math.max(1, Math.round(box.width * ratio));
      this.canvas.height = Math.max(1, Math.round(box.height * ratio));
      this.ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      this.layout();
    }

    // memories: [{id, title, compartment, strength, links}]
    setMemories(memories) {
      const next = new Map();
      next.set("@self", { id: "@self", kind: "self", title: this.labels.self, r: 15 });
      const compartments = [...new Set(memories.map((m) => m.compartment))].sort();
      compartments.forEach((name, i) => next.set("#" + name, {
        id: "#" + name, kind: "hub", title: name, r: 8, color: PALETTE[i % PALETTE.length] }));
      memories.forEach((m) => {
        const hub = next.get("#" + m.compartment);
        next.set(m.id, { id: m.id, kind: "memory", title: m.title, hub: hub.id, color: hub.color,
                         r: 3 + 5 * Math.max(0, Math.min(1, m.strength)), strength: m.strength });
      });
      // Keep positions of nodes that already existed, so the picture does not jump.
      next.forEach((node, id) => { const old = this.nodes.get(id); if (old) { node.x = old.x; node.y = old.y; } });
      this.nodes = next;
      this.edges = [];
      compartments.forEach((name) => this.edges.push(["@self", "#" + name, 0.5]));
      memories.forEach((m) => {
        this.edges.push(["#" + m.compartment, m.id, 0.35]);
        (m.links || []).forEach((link) => { if (next.has(link)) this.edges.push([m.id, link, 0.22]); });
      });
      this.layout();
    }

    layout() {
      const cx = this.w / 2, cy = this.h / 2, scale = Math.min(this.w, this.h);
      const hubs = [...this.nodes.values()].filter((n) => n.kind === "hub");
      const place = (node, x, y) => { node.tx = x; node.ty = y; if (node.x === undefined) { node.x = cx; node.y = cy; } };
      const self = this.nodes.get("@self"); if (self) place(self, cx, cy);
      hubs.forEach((hub, i) => {
        const angle = -Math.PI / 2 + (2 * Math.PI * i) / Math.max(1, hubs.length);
        hub.angle = angle;
        place(hub, cx + Math.cos(angle) * scale * 0.2, cy + Math.sin(angle) * scale * 0.2);
        const kids = [...this.nodes.values()].filter((n) => n.hub === hub.id);
        const spread = Math.min(Math.PI * 0.9, (2 * Math.PI) / Math.max(1, hubs.length) * 0.92);
        kids.forEach((kid, k) => {
          const ring = 0.31 + 0.065 * (k % 3);
          const a = angle + (kids.length === 1 ? 0 : (k / (kids.length - 1) - 0.5) * spread);
          place(kid, cx + Math.cos(a) * scale * ring, cy + Math.sin(a) * scale * ring);
        });
      });
    }

    // A recall: light travels from the self, through the compartment, to the memory.
    recall(id) {
      const node = this.nodes.get(id);
      if (!node || node.kind !== "memory") return;
      this.pulses.push({ path: ["@self", node.hub, id], at: performance.now(), color: node.color });
    }
    // Something reached the stage: the self lights up.
    stage() { this.ripples.push({ at: performance.now() }); }

    pick(event) {
      const box = this.canvas.getBoundingClientRect();
      const x = event.clientX - box.left, y = event.clientY - box.top;
      let best = null, bestD = 16;
      this.nodes.forEach((n) => { const d = Math.hypot(n.x - x, n.y - y) - n.r; if (d < bestD) { best = n; bestD = d; } });
      this.hover = best;
      if (best) {
        this.tip.textContent = best.title; this.tip.hidden = false;
        this.tip.style.left = Math.min(x + 14, this.w - 200) + "px"; this.tip.style.top = y + 14 + "px";
      } else this.tip.hidden = true;
    }

    frame(now) {
      if (!this.running) return;
      const ctx = this.ctx, style = getComputedStyle(document.documentElement);
      const ink = style.getPropertyValue("--text").trim(), accent = style.getPropertyValue("--accent").trim();
      const faint = style.getPropertyValue("--text-3").trim();
      ctx.clearRect(0, 0, this.w, this.h);
      const t = (now - this.t0) / 1000;
      this.nodes.forEach((n, id) => {
        const drift = n.kind === "self" ? 0 : 3;
        const phase = id.length * 1.7;
        const gx = n.tx + Math.sin(t * 0.5 + phase) * drift, gy = n.ty + Math.cos(t * 0.4 + phase) * drift;
        n.x += (gx - n.x) * 0.06; n.y += (gy - n.y) * 0.06;
      });

      ctx.lineCap = "round";
      this.edges.forEach(([a, b, alpha]) => {
        const p = this.nodes.get(a), q = this.nodes.get(b); if (!p || !q) return;
        ctx.globalAlpha = alpha * 0.55; ctx.strokeStyle = faint; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
      });
      ctx.globalAlpha = 1;

      this.ripples = this.ripples.filter((r) => now - r.at < 1400);
      const self = this.nodes.get("@self");
      this.ripples.forEach((r) => {
        const k = (now - r.at) / 1400;
        ctx.globalAlpha = (1 - k) * 0.5; ctx.strokeStyle = accent; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(self.x, self.y, self.r + k * 46, 0, Math.PI * 2); ctx.stroke();
      });
      ctx.globalAlpha = 1;

      const lit = new Map();
      this.pulses = this.pulses.filter((p) => now - p.at < 2600);
      this.pulses.forEach((p) => {
        const k = (now - p.at) / 1500, segs = p.path.length - 1;
        if (k < 1) {
          const pos = k * segs, i = Math.min(segs - 1, Math.floor(pos)), f = pos - i;
          const a = this.nodes.get(p.path[i]), b = this.nodes.get(p.path[i + 1]);
          if (a && b) {
            const x = a.x + (b.x - a.x) * f, y = a.y + (b.y - a.y) * f;
            const glow = ctx.createRadialGradient(x, y, 0, x, y, 16);
            glow.addColorStop(0, p.color); glow.addColorStop(1, "transparent");
            ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(x, y, 16, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(x, y, 2.4, 0, Math.PI * 2); ctx.fill();
          }
        } else lit.set(p.path[segs], 1 - (k - 1) / 0.75);
      });

      this.nodes.forEach((n) => {
        const glowing = Math.max(0, lit.get(n.id) || 0), hovered = this.hover === n;
        const color = n.kind === "self" ? accent : n.color;
        if (glowing > 0 || n.kind === "self") {
          const radius = n.r + 14 + glowing * 14;
          const glow = ctx.createRadialGradient(n.x, n.y, n.r * 0.5, n.x, n.y, radius);
          glow.addColorStop(0, color); glow.addColorStop(1, "transparent");
          ctx.globalAlpha = n.kind === "self" ? 0.35 + 0.1 * Math.sin(t * 1.2) : 0.75 * glowing;
          ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(n.x, n.y, radius, 0, Math.PI * 2); ctx.fill();
        }
        ctx.globalAlpha = n.kind === "memory" ? 0.45 + 0.55 * Math.max(0, Math.min(1, n.strength)) : 1;
        ctx.fillStyle = color; ctx.beginPath(); ctx.arc(n.x, n.y, n.r + (hovered ? 2 : 0), 0, Math.PI * 2); ctx.fill();
        ctx.globalAlpha = 1;
        if (n.kind !== "memory") {
          ctx.fillStyle = n.kind === "self" ? ink : faint;
          ctx.font = (n.kind === "self" ? "600 12px " : "11px ") + getComputedStyle(document.body).fontFamily;
          ctx.textAlign = "center";
          ctx.fillText(n.title, n.x, n.y + n.r + 15);
        }
      });
      requestAnimationFrame((time) => this.frame(time));
    }
  }

  window.Brain = Brain;
})();
