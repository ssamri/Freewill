// Freewill interface. Everything shown here comes from the being's real event
// stream and life file; nothing is decorative. Text coming from the being or
// the person is always inserted as text, never as markup.
(function () {
  "use strict";

  const TOKEN = document.querySelector('meta[name="freewill-token"]').content;
  const root = document.getElementById("root");
  const store = {
    get(key, fallback) { try { return localStorage.getItem(key) || fallback; } catch (_) { return fallback; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch (_) { /* private mode */ } },
  };

  const S = {
    lang: store.get("fw-lang", (navigator.language || "en").toLowerCase().startsWith("fr") ? "fr" : "en"),
    theme: store.get("fw-theme", "system"),
    view: "chat",
    snap: null, seq: 0, run: 0,
    chat: [], moments: [], current: null, ticker: "",
    memories: [], memLoaded: false, comp: null, memId: null, memItem: null,
    keys: {},
  };

  // ---------- helpers ----------

  function t(path, vars) {
    let node = window.I18N[S.lang];
    for (const part of path.split(".")) node = node == null ? undefined : node[part];
    if (typeof node !== "string") return path;
    return node.replace(/\{(\w+)\}/g, (_, k) => (vars && vars[k] != null ? vars[k] : ""));
  }
  function tr(path) { let n = window.I18N[S.lang]; for (const p of path.split(".")) n = n && n[p]; return n; }

  function h(tag, props, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) {
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else if (k === "value") el.value = v;
      else if (v === true) el.setAttribute(k, "");
      else el.setAttribute(k, v);
    }
    for (const kid of kids.flat()) {
      if (kid == null || kid === false) continue;
      el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    }
    return el;
  }

  const ICONS = {
    chat: '<path d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v7a2.5 2.5 0 0 1-2.5 2.5H10l-4.5 3.5V16A2.5 2.5 0 0 1 4 13.5z"/>',
    subconscious: '<path d="M3 9c2.5-3 4.5-3 7 0s4.5 3 7 0 3-2 4-1"/><path d="M3 15c2.5-3 4.5-3 7 0s4.5 3 7 0 3-2 4-1"/>',
    memory: '<path d="M4 7.5 12 4l8 3.5-8 3.5z"/><path d="m4 12 8 3.5 8-3.5"/><path d="m4 16.5 8 3.5 8-3.5"/>',
    brain: '<circle cx="12" cy="12" r="2.2"/><circle cx="5" cy="6" r="1.6"/><circle cx="19" cy="6.5" r="1.6"/><circle cx="6" cy="18.5" r="1.6"/><circle cx="18.5" cy="18" r="1.6"/><path d="m10.3 10.6-4-3.4M13.8 10.7l4-3.1M10.5 13.6l-3.4 3.7M13.7 13.5l3.6 3.4"/>',
    state: '<path d="M3 12h4l2.5-6 4 12 2.5-6h5"/>',
    milestones: '<path d="M6 4h10a2 2 0 0 1 2 2v14l-7-3.5L4 20V6a2 2 0 0 1 2-2z"/>',
    dreams: '<path d="M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M12 3v2.5M12 18.5V21M3 12h2.5M18.5 12H21M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M5.6 18.4l1.8-1.8M16.6 7.4l1.8-1.8"/>',
    theme: '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5v17a8.5 8.5 0 0 0 0-17z" fill="currentColor"/>',
  };
  function icon(name) {
    const span = document.createElement("span");
    span.style.display = "contents";
    span.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' + ICONS[name] + "</svg>"; // static markup only
    return span.firstChild;
  }

  async function api(path, body) {
    const options = { headers: { "X-Freewill-Token": TOKEN } };
    if (body !== undefined) {
      options.method = "POST";
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) { const e = new Error(data.error || response.statusText); e.status = response.status; throw e; }
    return data;
  }

  function applyTheme() {
    const dark = S.theme === "dark" || (S.theme === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    document.documentElement.lang = S.lang;
  }
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", applyTheme);

  function clock(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    return isNaN(d) ? "" : d.toLocaleTimeString(S.lang, { hour: "2-digit", minute: "2-digit" });
  }
  function day(iso) {
    const d = new Date(iso);
    return isNaN(d) ? "" : d.toLocaleString(S.lang, { dateStyle: "long", timeStyle: "short" });
  }
  function sourceLabel(source) { return (tr("sources") || {})[source] || source; }
  function pct(x) { return Math.round(100 * Math.max(0, Math.min(1, x))) + " %"; }
  function bar(x) { return h("div", { class: "bar" }, h("i", { style: "width:" + Math.round(100 * Math.max(0, Math.min(1, x))) + "%" })); }

  // ---------- welcome and birth ----------

  async function showWelcome() {
    S.run++; S.snap = null;
    let info = { lives: [], keys: {} };
    try { info = await api("/api/lives"); } catch (_) { /* shown empty */ }
    S.keys = info.keys || {};
    const W = { step: 0, name: "", you: "", lang: S.lang, kind: "local", model: "", key: "", error: "", busy: false, born: null };

    function draw() {
      const card = h("div", { class: "welcome-card glass" });
      const steps = h("div", { class: "steps" }, [0, 1, 2, 3].map((i) => h("i", { class: i <= W.step ? "on" : "" })));
      const error = W.error ? h("div", { class: "error", role: "alert" }, W.error) : "";

      if (W.step === 0) {
        card.append(
          h("div", { class: "brand", style: "padding:0" }, h("i", { class: "brand-mark" }), h("span", {}, "Freewill")),
          h("h1", {}, t("welcome.lead")),
          h("p", {}, t("welcome.caveat")));
        if (info.lives.length) {
          card.append(h("div", { class: "section-title" }, t("welcome.who")));
          info.lives.forEach((life) => card.append(h("button", { class: "life-row", onclick: () => wake(life.name) },
            h("i", { class: "orb" }),
            h("div", {}, h("b", {}, life.name), h("div", { class: "small muted" }, t("born_ago", { age: life.age }))),
            h("span", { class: "tag neutral", style: "margin-left:auto" }, life.engine || ""))));
        }
        card.append(error, h("div", { class: "actions" },
          h("button", { class: "icon-btn", title: t("theme"), "aria-label": t("theme"), onclick: toggleTheme }, icon("theme")),
          h("button", { class: "btn primary", onclick: () => { W.step = 1; W.error = ""; draw(); } }, t("welcome.new"))));
      } else if (W.step === 1) {
        const name = h("input", { id: "w-name", value: W.name, maxlength: 40, autocomplete: "off", oninput: (e) => { W.name = e.target.value; } });
        card.append(steps, h("h1", {}, t("welcome.s2")), h("p", {}, t("welcome.s2_lead")),
          h("div", { class: "field" }, h("label", { for: "w-name" }, t("welcome.name")), name),
          h("div", { class: "row" },
            h("div", { class: "field" }, h("label", { for: "w-you" }, t("welcome.you")),
              h("input", { id: "w-you", value: W.you, maxlength: 40, autocomplete: "off", oninput: (e) => { W.you = e.target.value; } })),
            h("div", { class: "field" }, h("label", { for: "w-lang" }, t("welcome.lang")),
              h("select", { id: "w-lang", onchange: (e) => { W.lang = e.target.value; } },
                h("option", { value: "fr", selected: W.lang === "fr" }, "Français"),
                h("option", { value: "en", selected: W.lang === "en" }, "English")))),
          error, h("div", { class: "actions" },
            h("button", { class: "btn", onclick: () => { W.step = 0; W.error = ""; draw(); } }, t("welcome.back")),
            h("button", { class: "btn primary", onclick: () => {
              if (!/^\p{L}[\p{L}\p{N} '\-]{0,39}$/u.test(W.name.trim())) { W.error = t("errors.name"); return draw(); }
              W.step = 2; W.error = ""; draw();
            } }, t("welcome.next"))));
        setTimeout(() => name.focus(), 0);
      } else if (W.step === 2) {
        card.append(steps, h("h1", {}, t("welcome.s3")), h("p", {}, t("welcome.s3_lead")));
        ["own", "local", "anthropic", "openai", "xai", "simulated"].forEach((kind) => {
          const [title, text] = tr("welcome.engines")[kind];
          card.append(h("button", { class: "choice" + (W.kind === kind ? " on" : ""), disabled: kind === "own",
            "aria-pressed": String(W.kind === kind), onclick: () => { W.kind = kind; W.error = ""; draw(); } },
            h("div", {}, h("b", {}, title), h("span", {}, text))));
        });
        if (W.kind !== "simulated") {
          const needsKey = W.kind !== "local";
          card.append(h("div", { class: "row", style: "margin-top:14px" },
            h("div", { class: "field" }, h("label", { for: "w-model" }, t("welcome.model")),
              h("input", { id: "w-model", value: W.model, autocomplete: "off", spellcheck: "false",
                placeholder: W.kind === "anthropic" ? "claude-opus-5-5" : "", oninput: (e) => { W.model = e.target.value; } }),
              h("span", { class: "hint" }, t("welcome.model_hint"))),
            needsKey ? h("div", { class: "field" }, h("label", { for: "w-key" }, t("set.key")),
              h("input", { id: "w-key", type: "password", value: W.key, autocomplete: "off",
                placeholder: S.keys[W.kind] ? "••••••••" : "", oninput: (e) => { W.key = e.target.value; } }),
              h("span", { class: "hint" }, S.keys[W.kind] ? t("set.key_set") : t("set.key_hint"))) : null));
        }
        card.append(error, h("div", { class: "actions" },
          h("button", { class: "btn", onclick: () => { W.step = 1; W.error = ""; draw(); } }, t("welcome.back")),
          h("button", { class: "btn primary", disabled: W.busy, onclick: birth }, t("welcome.birth"))));
      } else {
        const snap = W.born, names = tr("state.names"), genders = tr("state.genders");
        card.append(steps, h("h1", {}, t("welcome.s4", { name: snap.name })), h("p", {}, t("welcome.s4_lead")),
          h("div", { class: "card" },
            h("div", { class: "meter" }, h("span", {}, t("state.gender")), h("span", {}), h("span", { style: "white-space:nowrap" }, genders[snap.gender] || snap.gender)),
            Object.entries(snap.genome).filter(([, v]) => typeof v === "number").map(([k, v]) =>
              h("div", { class: "meter" }, h("span", {}, names[k] || k), bar(v), h("span", {}, pct(v))))),
          h("div", { class: "actions" }, h("span", {}),
            h("button", { class: "btn primary", onclick: () => enter(snap) }, t("welcome.enter", { name: snap.name }))));
      }
      root.replaceChildren(h("div", { class: "welcome" }, card));
    }

    async function birth() {
      W.busy = true; W.error = ""; draw();
      try {
        const engine = { kind: W.kind };
        if (W.model.trim()) engine.model = W.model.trim();
        W.born = await api("/api/birth", { name: W.name.trim(), interlocutor: W.you.trim(), language: W.lang,
                                           engine, api_key: W.key.trim() || undefined });
        W.key = ""; W.step = 3;
      } catch (e) { W.error = t("errors.generic", { message: e.message }); }
      W.busy = false; draw();
    }
    async function wake(name) {
      try { enter(await api("/api/wake", { name })); }
      catch (e) { W.error = t("errors.generic", { message: e.message }); draw(); }
    }
    draw();
  }

  // ---------- the being's events ----------

  function enter(snap) {
    Object.assign(S, { snap, seq: 0, chat: [], moments: [], current: null, ticker: "", memories: [],
                       memLoaded: false, comp: null, memId: null, memItem: null, view: "chat" });
    const run = ++S.run;
    drawShell();
    loadMemories();
    poll(run);
  }

  async function poll(run) {
    let failures = 0;
    while (run === S.run) {
      try {
        const data = await api("/api/events?since=" + S.seq);
        if (run !== S.run) return;
        failures = 0;
        S.snap = data.snapshot;
        let memoryChanged = false;
        for (const event of data.events) {
          S.seq = Math.max(S.seq, event.seq);
          memoryChanged = absorb(event) || memoryChanged;
        }
        if (memoryChanged) loadMemories();
        refresh();
      } catch (e) {
        if (run !== S.run) return;
        if (e.status === 409 || e.status === 401) return showWelcome();
        failures++;
        await new Promise((r) => setTimeout(r, Math.min(8000, 500 * failures)));
      }
    }
  }

  // Fold one event into what the views show. Returns true if memory changed.
  function absorb(event) {
    const d = event.data || {}, past = !!event.past, m = S.current;
    switch (event.type) {
      case "heard": S.chat.push({ who: "other", text: d.text }); break;
      case "stage":
        S.current = { kind: "stage", time: event.time, past, source: d.source, text: d.text, salience: d.salience,
                      below: d.below || [], recalls: [], extras: [] };
        S.moments.push(S.current);
        if (!past) { pulse(); if (brain) brain.stage(); }
        break;
      case "recall":
        if (m) m.recalls.push(d.title);
        if (!past && brain) brain.recall(d.id);
        break;
      case "decision":
        if (m) { m.accepted = d.accepted; m.reason = d.reason; m.thought = d.thought; }
        if (d.thought) S.ticker = d.thought;
        break;
      case "speech":
        S.chat.push({ who: "self", text: d.text, spontaneous: d.spontaneous });
        if (m) m.said = d.text;
        break;
      case "silence":
        S.chat.push({ who: "note", text: t("chat.silent", { name: S.snap.name }) });
        if (m) m.silent = true;
        break;
      case "remember": if (m) m.extras.push(t("sub.keeps") + " : " + d.title); return true;
      case "value": if (m) m.extras.push(t("sub.value") + " : " + d.text); break;
      case "milestone": if (m) m.extras.push(t("sub.first") + " : " + (tr("miles")[d.name] || d.name)); break;
      case "rest":
        S.moments.push({ kind: "rest", time: event.time, past, faded: d.faded });
        S.current = null;
        return true;
      case "kernel_refusal": case "engine_error": case "engine_refusal":
        if (m) m.extras.push(d.message);
        break;
    }
    if (S.moments.length > 300) S.moments.splice(0, S.moments.length - 300);
    if (S.chat.length > 500) S.chat.splice(0, S.chat.length - 500);
    return false;
  }

  async function loadMemories() {
    const run = S.run;
    try {
      const data = await api("/api/memory");
      if (run !== S.run) return;
      S.memories = data.memories; S.memLoaded = true;
      if (brain) brain.setMemories(S.memories);
      if (S.view === "memory" || S.view === "brain") refresh();
    } catch (_) { /* next event will retry */ }
  }

  // ---------- shell ----------

  const NAV = ["chat", "subconscious", "memory", "brain", "state", "milestones", "dreams", "settings"];
  let ui = {}, brain = null, view = null;

  function drawShell() {
    applyTheme();
    ui = {};
    ui.orb = h("i", { class: "orb" });
    ui.name = h("div", { class: "being-name" });
    ui.age = h("div", { class: "being-age" });
    ui.nav = h("nav", { class: "nav" }, NAV.map((id) =>
      h("button", { "data-view": id, onclick: () => go(id) }, icon(id), h("span", {}, t("nav." + id)),
        id === "dreams" ? h("span", { class: "soon" }, t("soon")) : null)));
    ui.engine = h("div", { class: "engine-badge" });
    ui.title = h("h1", {});
    ui.tickerText = h("span", { class: "ticker-text" });
    ui.banner = h("div", { class: "banner", role: "status", hidden: true });
    ui.view = h("div", { class: "view" });
    root.replaceChildren(h("div", { class: "shell" },
      h("aside", { class: "sidebar glass" },
        h("div", { class: "brand" }, h("i", { class: "brand-mark" }), h("span", {}, "Freewill")),
        h("div", { class: "being" }, ui.orb, h("div", { style: "min-width:0" }, ui.name, ui.age)),
        ui.nav,
        h("div", { class: "sidebar-foot" }, ui.engine,
          h("button", { class: "icon-btn", title: t("theme"), "aria-label": t("theme"), onclick: toggleTheme }, icon("theme")))),
      h("main", { class: "main glass" },
        h("header", { class: "main-head" }, ui.title, h("div", { class: "ticker" }, ui.tickerText)),
        ui.banner, ui.view)));
    go(S.view);
  }

  function toggleTheme() {
    S.theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    store.set("fw-theme", S.theme);
    applyTheme();
    if (S.snap && S.view === "settings") go("settings");
  }

  function pulse() {
    if (!ui.orb) return;
    ui.orb.classList.remove("thinking");
    void ui.orb.offsetWidth; // restart the animation
    ui.orb.classList.add("thinking");
  }

  function go(id) {
    S.view = id;
    if (brain) { brain.destroy(); brain = null; }
    ui.nav.querySelectorAll("button").forEach((b) => {
      const on = b.dataset.view === id;
      b.classList.toggle("active", on);
      if (on) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
    });
    ui.title.textContent = t("nav." + id);
    ui.view.className = "view" + (["chat", "memory", "brain"].includes(id) ? " flush" : "");
    ui.view.replaceChildren();
    view = VIEWS[id]();
    refresh();
  }

  function refresh() {
    const snap = S.snap;
    if (!snap || !ui.view) return;
    ui.name.textContent = snap.name;
    ui.age.textContent = t("born_ago", { age: snap.age });
    ui.engine.textContent = snap.engine.name || snap.engine.kind || "";
    ui.engine.title = ui.engine.textContent;
    ui.tickerText.textContent = S.ticker;
    ui.banner.hidden = !snap.paused;
    ui.banner.textContent = snap.paused ? t("paused", { reason: snap.paused }) : "";
    const last = S.moments[S.moments.length - 1];
    ui.orb.classList.toggle("resting", !!last && last.kind === "rest");
    if (view && view.update) view.update();
  }

  // ---------- views ----------

  const VIEWS = {
    chat() {
      const scroll = h("div", { class: "chat-scroll", role: "log", "aria-live": "polite" });
      const input = h("textarea", { rows: 1, "aria-label": t("chat.placeholder", { name: S.snap.name }),
                                    placeholder: t("chat.placeholder", { name: S.snap.name }) });
      const send = async () => {
        const text = input.value.trim();
        if (!text) return;
        input.value = ""; input.style.height = "";
        try { await api("/api/message", { text }); } catch (e) { input.value = text; }
      };
      input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); } });
      input.addEventListener("input", () => { input.style.height = ""; input.style.height = Math.min(160, input.scrollHeight) + "px"; });
      ui.view.append(scroll, h("div", { class: "composer" }, input, h("button", { class: "btn primary", onclick: send }, t("chat.send"))));
      setTimeout(() => input.focus(), 0);
      let shown = -1;
      return { update() {
        if (shown === S.chat.length) return;
        const stick = scroll.scrollHeight - scroll.scrollTop - scroll.clientHeight < 80 || shown < 0;
        shown = S.chat.length;
        if (!S.chat.length) {
          scroll.replaceChildren(h("div", { class: "empty" }, h("p", {}, t("chat.empty", { name: S.snap.name }))));
          return;
        }
        scroll.replaceChildren(...S.chat.map((m) => m.who === "note"
          ? h("div", { class: "msg-note" }, m.text)
          : h("div", { class: "msg " + m.who + (m.spontaneous ? " spontaneous" : ""),
                       title: m.spontaneous ? t("chat.spontaneous") : null }, m.text)));
        if (stick) scroll.scrollTop = scroll.scrollHeight;
      } };
    },

    subconscious() {
      let shown = "";
      return { update() {
        const last = S.moments[S.moments.length - 1];
        const stamp = S.moments.length + ":" + JSON.stringify(last || 0).length;
        if (stamp === shown) return;
        shown = stamp;
        if (!S.moments.length) return ui.view.replaceChildren(h("div", { class: "empty" }, h("p", {}, t("sub.empty"))));
        ui.view.replaceChildren(...S.moments.slice().reverse().map((m) => {
          if (m.kind === "rest") {
            return h("div", { class: "moment" + (m.past ? " past" : "") }, h("div", { class: "moment-head", style: "margin:0" },
              h("span", { class: "tag neutral" }, t("sub.rest", { n: m.faded == null ? 0 : m.faded })), h("time", {}, clock(m.time))));
          }
          const verdict = m.accepted == null ? null : h("div", { class: "moment-verdict" },
            h("span", { class: "tag " + (m.accepted ? "good" : "bad") }, m.accepted ? t("sub.welcomed") : t("sub.dismissed")),
            h("span", {}, m.reason || ""));
          const extras = [
            ...m.recalls.map((title) => t("sub.recalls") + " : " + title),
            m.said ? t("sub.said") + " : « " + m.said + " »" : null,
            m.silent ? t("sub.silent") : null,
            ...m.extras,
          ].filter(Boolean);
          return h("article", { class: "moment" + (m.past ? " past" : "") },
            h("div", { class: "moment-head" }, h("span", { class: "tag" }, sourceLabel(m.source)),
              h("div", { class: "salience", title: pct(m.salience) }, bar(m.salience)), h("time", {}, clock(m.time))),
            h("div", { class: "moment-text" }, m.text),
            verdict,
            m.thought ? h("div", { class: "moment-thought" }, m.thought) : null,
            extras.length ? h("div", { class: "moment-extra" }, extras.map((x) => h("span", {}, x))) : null,
            m.below.length ? h("div", { class: "below" }, h("span", { class: "hint" }, t("sub.below")),
              m.below.map((b) => h("div", { class: "below-row" }, h("span", { class: "tag neutral" }, sourceLabel(b.source)),
                bar(b.salience), h("span", { title: b.text }, b.text)))) : null);
        }));
      } };
    },

    memory() {
      const cols = [h("div", {}), h("div", {}), h("div", {})];
      ui.view.append(h("div", { class: "memory" }, cols));
      async function open(id) {
        S.memId = id; S.memItem = null; draw();
        try { S.memItem = await api("/api/memory/item?id=" + encodeURIComponent(id)); } catch (_) { S.memId = null; }
        draw();
      }
      function draw() {
        if (!S.memories.length) {
          cols[0].replaceChildren(); cols[2].replaceChildren();
          cols[1].replaceChildren(h("div", { class: "empty" }, h("p", {}, S.memLoaded ? t("mem.empty", { name: S.snap.name }) : "…")));
          return;
        }
        const counts = {};
        S.memories.forEach((m) => { counts[m.compartment] = (counts[m.compartment] || 0) + 1; });
        const comp = (name, label, n) => h("button", { class: "comp" + (S.comp === name ? " active" : ""),
          onclick: () => { S.comp = name; draw(); } }, h("span", {}, label), h("span", { class: "faint" }, n));
        cols[0].replaceChildren(comp(null, t("mem.all"), S.memories.length),
          ...Object.keys(counts).sort().map((name) => comp(name, name, counts[name])));
        const list = S.memories.filter((m) => !S.comp || m.compartment === S.comp)
          .sort((a, b) => (b.date || "").localeCompare(a.date || ""));
        cols[1].replaceChildren(...list.map((m) => h("button", { class: "mem" + (S.memId === m.id ? " active" : ""), onclick: () => open(m.id) },
          h("div", { class: "mem-title" }, m.title), h("div", { class: "mem-sum" }, m.summary), bar(m.strength))));
        const it = S.memItem;
        if (!it) return cols[2].replaceChildren(h("div", { class: "empty" }, h("p", {}, S.memId ? "…" : t("mem.pick"))));
        const states = tr("mem.states");
        cols[2].replaceChildren(
          h("h2", { style: "font-size:18px" }, it.title),
          h("p", { class: "muted", style: "margin-top:4px" }, it.summary),
          h("div", { class: "mem-body" }, it.body && it.body.trim() ? it.body : h("span", { class: "faint" }, t("mem.lost"))),
          h("div", { class: "kv" },
            h("b", {}, t("mem.date")), h("span", {}, day(it.date)),
            h("b", {}, t("mem.state")), h("span", {}, (states[it.state] || it.state) + (it.kept ? " · " + t("mem.kept") : "")),
            h("b", {}, t("mem.strength")), h("span", {}, pct(it.strength)),
            h("b", {}, t("mem.importance")), h("span", {}, pct(it.importance)),
            it.tags && it.tags.length ? [h("b", {}, t("mem.tags")), h("span", {}, it.tags.join(", "))] : null,
            it.links && it.links.length ? [h("b", {}, t("mem.links")), h("span", {}, it.links.join(", "))] : null));
      }
      let shown = null;
      return { update() { if (shown !== S.memories) { shown = S.memories; draw(); } } };
    },

    brain() {
      const canvas = h("canvas", { role: "img", "aria-label": t("brain.legend") });
      const tip = h("div", { class: "brain-tip", hidden: true });
      const legend = h("div", { class: "brain-legend" });
      ui.view.append(h("div", { class: "brain" }, canvas, legend, tip));
      brain = new window.Brain(canvas, tip, { self: t("brain.self") });
      brain.setMemories(S.memories);
      return { update() {
        legend.textContent = S.memories.length ? t("brain.legend") : t("brain.empty", { name: S.snap.name });
      } };
    },

    state() {
      let shown = "";
      return { update() {
        const snap = S.snap, names = tr("state.names"), genders = tr("state.genders");
        const stamp = JSON.stringify([snap.needs, snap.values, snap.weights, snap.thoughts]);
        if (stamp === shown) return;
        shown = stamp;
        const meters = (obj) => Object.entries(obj).filter(([, v]) => typeof v === "number").map(([k, v]) =>
          h("div", { class: "meter" }, h("span", {}, names[k] || k), bar(v), h("span", {}, pct(v))));
        const weights = Object.entries(snap.weights);
        ui.view.replaceChildren(h("div", { class: "grid-2" },
          h("section", { class: "card" }, h("div", { class: "section-title" }, t("state.needs")), meters(snap.needs)),
          h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("state.temperament")), meters(snap.genome),
            h("div", { class: "kv" }, h("b", {}, t("state.gender")), h("span", {}, genders[snap.gender] || snap.gender || ""),
              h("b", {}, t("state.thoughts")), h("span", {}, snap.thoughts),
              h("b", {}, t("state.kernel")), h("span", { style: "font-family:ui-monospace,Consolas,monospace" }, snap.kernel))),
          h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("state.questions")),
            snap.questions.map((q) => h("p", { style: "padding:3px 0" }, q))),
          h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("state.values")),
            snap.values.length ? snap.values.map((v) => h("p", { style: "padding:3px 0" }, v.text))
                               : h("p", { class: "muted" }, t("state.no_values"))),
          weights.length ? h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("state.weights")),
            weights.map(([k, v]) => h("div", { class: "meter" }, h("span", {}, sourceLabel(k)), bar((v - 0.5)), h("span", {}, "× " + v.toFixed(2)))),
            h("p", { class: "hint", style: "margin-top:8px" }, t("state.weights_hint"))) : null));
      } };
    },

    milestones() {
      let shown = "";
      return { update() {
        const snap = S.snap, stamp = JSON.stringify(snap.milestones);
        if (stamp === shown) return;
        shown = stamp;
        const order = ["first_thought", "first_refusal", "first_memory", "first_spontaneous_word", "first_silence", "first_value"];
        const done = order.filter((k) => snap.milestones[k]).sort((a, b) => snap.milestones[a].localeCompare(snap.milestones[b]));
        ui.view.replaceChildren(h("div", { class: "timeline" },
          h("div", { class: "tl" }, h("b", {}, t("miles.birth")), h("span", { class: "small muted" }, day(snap.born))),
          done.map((k) => h("div", { class: "tl" }, h("b", {}, t("miles." + k)), h("span", { class: "small muted" }, day(snap.milestones[k])))),
          order.filter((k) => !snap.milestones[k]).map((k) =>
            h("div", { class: "tl pending" }, h("b", {}, t("miles." + k)), h("span", { class: "small" }, t("miles.not_yet"))))));
      } };
    },

    dreams() {
      ui.view.append(h("div", { class: "empty" }, h("div", {},
        h("h2", { style: "font-size:18px;margin-bottom:10px;color:var(--text)" }, t("dreams.title")),
        h("p", {}, t("dreams.body", { name: S.snap.name })))));
      return {};
    },

    settings() {
      const snap = S.snap, kind = snap.engine.kind;
      const saved = h("span", { class: "small muted", role: "status" });
      const flash = () => { saved.textContent = t("set.saved"); setTimeout(() => { saved.textContent = ""; }, 1800); };
      const select = (id, value, options, onchange) => h("select", { id, onchange: (e) => onchange(e.target.value) },
        options.map(([v, label]) => h("option", { value: v, selected: v === value }, label)));
      const number = (id, value, min, max, key) => h("input", { id, type: "number", min, max, value,
        onchange: async (e) => { try { S.snap = await api("/api/settings", { [key]: Number(e.target.value) }); flash(); } catch (_) { /* kept */ } } });
      const keyInput = h("input", { id: "s-key", type: "password", autocomplete: "off" });
      const keyState = h("span", { class: "hint" }, S.keys[kind] ? t("set.key_set") : t("set.key_none"));
      const takesKey = ["anthropic", "openai", "xai", "compatible"].includes(kind);
      ui.view.append(h("div", { class: "grid-2" },
        h("section", { class: "card" }, h("div", { class: "section-title" }, t("set.appearance")),
          h("div", { class: "field" }, h("label", { for: "s-theme" }, t("set.theme")),
            select("s-theme", S.theme, [["system", t("set.system")], ["light", t("set.light")], ["dark", t("set.dark")]],
              (v) => { S.theme = v; store.set("fw-theme", v); applyTheme(); })),
          h("div", { class: "field" }, h("label", { for: "s-lang" }, t("set.language")),
            select("s-lang", S.lang, [["fr", "Français"], ["en", "English"]],
              (v) => { S.lang = v; store.set("fw-lang", v); drawShell(); }))),
        h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("set.rhythm")),
          h("div", { class: "row" },
            h("div", { class: "field" }, h("label", { for: "s-tempo" }, t("set.tempo")), number("s-tempo", snap.tempo, 2, 3600, "tempo")),
            h("div", { class: "field" }, h("label", { for: "s-hour" }, t("set.per_hour")), number("s-hour", snap.thoughts_per_hour, 0, 3600, "thoughts_per_hour"))),
          h("p", { class: "hint" }, t("set.rhythm_hint")), saved),
        h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("set.engine")),
          h("p", { style: "margin-bottom:12px" }, snap.engine.name || kind),
          takesKey ? [h("div", { class: "field" }, h("label", { for: "s-key" }, t("set.key")), keyInput, keyState),
            h("button", { class: "btn", onclick: async () => {
              if (!keyInput.value.trim()) return;
              try { S.keys = (await api("/api/key", { kind, key: keyInput.value.trim() })).keys; keyInput.value = ""; keyState.textContent = t("set.key_set"); }
              catch (e) { keyState.textContent = t("errors.generic", { message: e.message }); }
            } }, t("set.key_save")),
            h("p", { class: "hint", style: "margin-top:10px" }, t("set.key_hint"))] : null),
        h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("set.being")),
          h("button", { class: "btn", onclick: async () => { S.run++; try { await api("/api/rest", {}); } catch (_) { /* already resting */ } showWelcome(); } },
            t("set.rest")))));
      return {};
    },
  };

  // ---------- start ----------

  applyTheme();
  (async function start() {
    try {
      const info = await api("/api/lives");
      S.keys = info.keys || {};
      if (info.awake) return enter(await api("/api/snapshot"));
    } catch (_) { /* fall through to the welcome screen */ }
    showWelcome();
  })();
})();
