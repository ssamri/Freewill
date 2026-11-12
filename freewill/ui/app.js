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
    lang: store.get("fw-lang", "en"),  // English unless the person chose French
    theme: store.get("fw-theme", "system"),
    view: "chat",
    snap: null, seq: 0, run: 0,
    chat: [], moments: [], current: null, ticker: "",
    memories: [], memLoaded: false, comp: null, memId: null, memItem: null, memTab: "memories", memQuery: "",
    dreams: null, asleep: false, brainActivity: [],
    brainControls: { rotate: !matchMedia("(prefers-reduced-motion: reduce)").matches,
                     motion: !matchMedia("(prefers-reduced-motion: reduce)").matches, paused: false },
    affect: null, affectStale: true,
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
  // replaceChildren() writes a null child as the text "null"; conditional parts of a view are null when absent.
  function fill(el, ...kids) {
    el.replaceChildren(...kids.flat().filter((kid) => kid != null && kid !== false));
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
    attach: '<path d="M20 11.5 12.2 19.3a5 5 0 0 1-7.1-7.1l8.2-8.2a3.4 3.4 0 0 1 4.8 4.8l-8.1 8.1a1.8 1.8 0 0 1-2.5-2.5l7.4-7.4"/>',
    file: '<path d="M7 3.5h7l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 19V5A1.5 1.5 0 0 1 7.5 3.5z"/><path d="M14 3.5V8h4"/>',
    close: '<path d="m6 6 12 12M18 6 6 18"/>',
    sources: '<path d="M5 5.5A1.5 1.5 0 0 1 6.5 4H11v15H6.5A1.5 1.5 0 0 0 5 20.5z"/><path d="M19 5.5A1.5 1.5 0 0 0 17.5 4H13v15h4.5a1.5 1.5 0 0 1 1.5 1.5z"/>',
    lab: '<path d="M9.5 3.5h5M10.5 3.5v6L5 19a1.4 1.4 0 0 0 1.2 2h11.6A1.4 1.4 0 0 0 19 19l-5.5-9.5v-6"/><path d="M7.6 15h8.8" opacity=".55"/>',
    affect: '<path d="M3 17c3 0 3-10 6-10s3 12 6 12 3-7 6-7"/><path d="M3 21h18" opacity=".45"/>',
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
    if (brain && brain.setTheme) brain.setTheme();
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
  // The age is worded in the interface's language, whatever language the being was born in.
  function ageOf(item) {
    const born = Date.parse(item && item.born), words = tr("ages") || {};
    if (!Number.isFinite(born)) return (item && item.age) || "";
    const seconds = Math.max(0, (Date.now() - born) / 1000);
    for (const [size, one, many] of [[86400, "day", "days"], [3600, "hour", "hours"], [60, "minute", "minutes"]]) {
      if (seconds >= size) { const n = Math.floor(seconds / size); return n + " " + words[n === 1 ? one : many]; }
    }
    return words.moments;
  }
  function sourceLabel(source) { return (tr("sources") || {})[source] || source; }
  function pct(x) { return Math.round(100 * Math.max(0, Math.min(1, x))) + " %"; }
  function bar(x) { return h("div", { class: "bar" }, h("i", { style: "width:" + Math.round(100 * Math.max(0, Math.min(1, x))) + "%" })); }

  const brandMark = (style) => h("div", { class: "brand", style },
    h("i", { class: "brand-mark" }), h("span", {}, "Freewill"), h("span", { class: "tag neutral exp" }, t("exp")));

  // ---------- sources and embedded models ----------

  // A link the application shows: opened in the person's own browser, by the service,
  // which only accepts the addresses it has itself put on screen.
  function link(url, label) {
    return h("button", { class: "linkish", title: url, onclick: (e) => { e.stopPropagation(); api("/api/open", { url }).catch(() => {}); } }, label);
  }
  function gb(bytes) { return (bytes / 1e9).toLocaleString(S.lang, { maximumFractionDigits: 1 }) + " " + t("models.gb"); }
  const DOWNLOADING = (m) => m.progress && (m.progress.state === "downloading" || m.progress.state === "verifying");

  // The catalogue of models the application can run by itself: the person picks one,
  // downloads it, and sees who made it and under which licence.
  function modelPicker(selected, onSelect, inUse) {
    const box = h("div", { class: "models" }, h("p", { class: "hint" }, "…"));
    let data = null, timer = null, failure = "";
    async function load() {
      try { data = await api("/api/models"); failure = ""; }
      catch (e) { if (!data) failure = e.message; }
      draw();
    }
    async function act(path, id) {
      try { const out = await api(path, { id }); if (out.models) data.models = out.models; }
      catch (e) { data.error = t("errors.generic", { message: e.message }); }
      if (path.endsWith("delete") && selected === id) { selected = ""; onSelect(""); }
      await load();
    }
    function row(m) {
      const p = m.progress || {}, busy = DOWNLOADING(m), on = selected === m.id;
      const right = m.installed
        ? [h("button", { class: "btn small" + (on ? " primary" : ""), "aria-pressed": String(on),
            onclick: () => { selected = m.id; onSelect(m.id); draw(); } }, on ? t("models.chosen") : t("models.choose")),
           inUse === m.id ? null : h("button", { class: "icon-btn", title: t("models.delete"), "aria-label": t("models.delete") + " " + m.name,
            onclick: () => act("/api/models/delete", m.id) }, icon("close"))]
        : busy
          ? [h("span", { class: "small muted" }, p.state === "verifying" ? t("models.verifying") : pct(p.done / Math.max(1, p.total))),
             h("button", { class: "btn small", onclick: () => act("/api/models/cancel", m.id) }, t("models.cancel"))]
          : h("button", { class: "btn small", onclick: () => act("/api/models/download", m.id) },
              (p.state === "error" || p.state === "cancelled") && p.done ? t("models.resume") : t("models.download"));
      return h("div", { class: "model" + (on ? " on" : "") },
        h("div", { class: "model-main" },
          h("div", { class: "model-head" }, h("b", {}, m.name), h("span", { class: "tag neutral" }, t("models.tiers." + m.tier)),
            m.sees ? h("span", { class: "tag" }, t("models.sees")) : null,
            m.learns ? h("span", { class: "tag" }, t("models.learns")) : null,
            m.installed ? h("span", { class: "tag good" }, t("models.installed")) : null),
          h("div", { class: "small muted" }, t("models.needs", { size: gb(m.download_size), ram: m.ram_gb })),
          h("div", { class: "model-src" }, h("span", {}, m.author), link(m.licence_url, m.licence), link(m.source_url, t("models.source"))),
          busy ? bar(p.done / Math.max(1, p.total)) : null,
          p.state === "error" ? h("div", { class: "error", role: "alert" }, p.error) : null),
        h("div", { class: "model-act" }, right));
    }
    function draw() {
      clearTimeout(timer);
      if (!data) return box.replaceChildren(failure
        ? h("div", { class: "error", role: "alert" }, t("errors.generic", { message: failure }), " ",
            h("button", { class: "btn small", onclick: () => { failure = ""; draw(); load(); } }, t("models.retry")))
        : h("p", { class: "hint" }, "…"));
      const rt = data.runtime || {}, rp = rt.progress || {};
      const rtBusy = ["downloading", "verifying", "unpacking"].includes(rp.state);
      fill(box,
        rt.present ? null
          : rtBusy ? h("div", { class: "hint" }, t("models.runtime_fetching", { tag: rt.tag }), bar(rp.done / Math.max(1, rp.total)))
          : rp.state === "error" ? h("div", { class: "error", role: "alert" }, t("models.runtime_error", { message: rp.error }), " ",
              h("button", { class: "btn small", onclick: async () => { await api("/api/runtime/install", {}).catch(() => {}); load(); } }, t("models.retry")))
          : rt.can_fetch ? h("p", { class: "hint" }, t("models.runtime_later", { tag: rt.tag }))
          : h("p", { class: "error", role: "alert" }, t("models.no_runtime", { platform: rt.platform || "?" })),
        data.error ? h("p", { class: "error", role: "alert" }, data.error) : null,
        ...data.models.map(row),
        h("p", { class: "hint" }, t("models.hint")));
      data.error = "";
      if ((data.models.some(DOWNLOADING) || rtBusy) && box.isConnected) timer = setTimeout(load, 900);
    }
    load();
    return box;
  }

  // ---------- terms of use and licence, accepted before anything else ----------

  function showGate(consent) {
    const G = { step: 1, terms: false, licence: false, error: "" };
    function draw() {
      const card = h("div", { class: "welcome-card glass gate" });
      const check = (key, label) => h("label", { class: "check" },
        h("input", { type: "checkbox", checked: G[key], onchange: (e) => { G[key] = e.target.checked; draw(); } }), h("span", {}, label));
      card.append(brandMark("padding:0"), h("div", { class: "steps", style: "margin-top:14px" },
        [1, 2].map((i) => h("i", { class: i <= G.step ? "on" : "" }))), h("div", { class: "hint", style: "margin-top:8px" }, t("gate.step", { n: G.step })));
      if (G.step === 1) {
        card.append(h("h1", {}, t("gate.terms_title")), h("p", {}, t("gate.terms_lead")),
          h("div", { class: "scrollbox", tabindex: "0" }, tr("gate.terms").map(([title, text]) =>
            h("div", { class: "term" }, h("b", {}, title), h("p", {}, text)))),
          check("terms", t("gate.terms_check")),
          h("div", { class: "actions" },
            h("button", { class: "icon-btn", title: t("theme"), "aria-label": t("theme"), onclick: () => { toggleTheme(); } }, icon("theme")),
            h("button", { class: "btn primary", disabled: !G.terms, onclick: () => { G.step = 2; draw(); } }, t("gate.next"))));
      } else {
        card.append(h("h1", {}, t("gate.licence_title")), h("p", {}, t("gate.licence_lead")),
          h("pre", { class: "scrollbox licence", tabindex: "0" }, consent.licence),
          check("licence", t("gate.licence_check")),
          G.error ? h("div", { class: "error", role: "alert" }, G.error) : "",
          h("div", { class: "actions" },
            h("button", { class: "btn", onclick: () => { G.step = 1; draw(); } }, t("gate.back")),
            h("button", { class: "btn primary", disabled: !G.licence || !G.terms, onclick: async () => {
              try { await api("/api/consent", { terms: true, licence: true }); showWelcome(); }
              catch (e) { G.error = t("errors.generic", { message: e.message }); draw(); }
            } }, t("gate.accept"))));
      }
      root.replaceChildren(h("div", { class: "welcome" }, card));
    }
    draw();
  }

  // ---------- welcome and birth ----------

  async function showWelcome() {
    S.run++; S.snap = null;
    if (brain) { brain.destroy(); brain = null; }
    let info = { lives: [], keys: {} };
    try { info = await api("/api/lives"); } catch (_) { /* shown empty */ }
    S.keys = info.keys || {};
    const W = { step: 0, name: "", you: "", lang: S.lang, kind: "embedded", model: "", key: "", error: "", busy: false, born: null };

    function draw() {
      const card = h("div", { class: "welcome-card glass" });
      const steps = h("div", { class: "steps" }, [0, 1, 2, 3].map((i) => h("i", { class: i <= W.step ? "on" : "" })));
      const error = W.error ? h("div", { class: "error", role: "alert" }, W.error) : "";

      if (W.step === 0) {
        card.append(
          brandMark("padding:0"),
          h("h1", {}, t("welcome.lead")),
          h("p", {}, t("welcome.caveat")));
        if (info.lives.length) {
          card.append(h("div", { class: "section-title" }, t("welcome.who")));
          info.lives.forEach((life) => card.append(h("button", { class: "life-row", onclick: () => wake(life.name) },
            h("i", { class: "orb" }),
            h("div", {}, h("b", {}, life.name), h("div", { class: "small muted" }, t("born_ago", { age: ageOf(life) }))),
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
        ["embedded", "local", "anthropic", "openai", "xai", "simulated", "own"].forEach((kind) => {
          const [title, text] = tr("welcome.engines")[kind];
          card.append(h("button", { class: "choice" + (W.kind === kind ? " on" : ""), disabled: kind === "own",
            "aria-pressed": String(W.kind === kind), onclick: () => { W.kind = kind; W.model = ""; W.error = ""; draw(); } },
            h("div", {}, h("b", {}, title), h("span", {}, text))));
          if (kind === "embedded" && W.kind === "embedded") card.append(modelPicker(W.model, (id) => { W.model = id; }));
        });
        if (W.kind !== "simulated" && W.kind !== "embedded") {
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
      if (W.kind === "embedded" && !W.model) { W.error = t("models.pick_first"); return draw(); }
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
                       memLoaded: false, comp: null, memId: null, memItem: null, memTab: "memories", memQuery: "",
                       dreams: null, asleep: !!snap.sleeping, brainActivity: [], affect: null, affectStale: true, view: "chat" });
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
    if (["stage", "recall", "decision", "speech", "remember", "read", "sleep", "dream", "rest", "engine_error", "kernel_refusal"].includes(event.type)) {
      S.brainActivity.push(event);
      if (S.brainActivity.length > 8) S.brainActivity.shift();
    }
    switch (event.type) {
      case "heard": S.chat.push({ who: "other", text: d.text, attachments: d.attachments || [] }); break;
      case "stage":
        S.current = { kind: "stage", time: event.time, past, source: d.source, text: d.text, salience: d.salience,
                      below: d.below || [], recalls: [], extras: [] };
        S.moments.push(S.current);
        if (!past) { pulse(); if (brain) brain.stage(d.source, d.below, d.salience, d); }
        break;
      case "recall":
        if (m) m.recalls.push(d.title);
        if (!past && brain) brain.recall(d.id, d.path, d);
        if (!past && typeof d.strength === "number") {
          const header = { strength: d.strength, state: d.state, last_recall: event.time };
          S.memories = S.memories.map((item) => item.id === d.id
            ? { ...item, strength: d.strength, state: d.state || item.state, last_recall: event.time } : item);
          if (memoryFlight && memoryFlight.run === S.run) memoryFlight.headers.set(d.id, header);
        }
        // Older event logs do not carry the updated header. One coalesced fetch
        // covers a whole batch, rather than one request for each recall.
        return !past && typeof d.strength !== "number";
      case "decision":
        if (m) { m.accepted = d.accepted; m.reason = d.reason; m.thought = d.thought; }
        if (d.thought) S.ticker = d.thought;
        if (!past && brain) brain.decision(d.accepted, d);
        break;
      case "speech":
        S.chat.push({ who: "self", text: d.text, spontaneous: d.spontaneous });
        if (m) m.said = d.text;
        if (!past && brain) brain.speech(d);
        break;
      case "silence":
        S.chat.push({ who: "note", text: t("chat.silent", { name: S.snap.name }) });
        if (m) m.silent = true;
        break;
      case "remember":
        if (m) m.extras.push(t("sub.keeps") + " : " + d.title);
        if (!past && brain && brain.remember) brain.remember(d.id, d);
        return true;
      case "value": if (m) m.extras.push(t("sub.value") + " : " + d.text); break;
      case "milestone": if (m) m.extras.push(t("sub.first") + " : " + (tr("miles")[d.name] || d.name)); break;
      case "read":
        if (m) m.extras.push(t("sub.reads") + " : " + d.name + " (" + (d.last && d.last !== d.number ? d.number + "–" + d.last : d.number) + "/" + d.of + ")");
        if (!past && brain) brain.read(d);
        break;
      case "sleep":
        S.asleep = !past;
        S.moments.push({ kind: "note", time: event.time, past, text: t("sub.sleep") });
        S.current = null;
        break;
      case "dream":
        S.moments.push({ kind: "dream", time: event.time, past, title: d.title, text: d.text });
        S.dreams = null;
        if (!past) { S.ticker = d.text; if (brain) brain.dream(d.memories, d); if (S.view === "dreams") loadDreams(); }
        return true;
      case "rest":
        S.asleep = false;
        S.moments.push({ kind: "note", time: event.time, past, text: t("sub.woke", { d: d.dreams || 0, n: d.faded || 0 }) });
        S.current = null;
        return true;
      case "affect_transition": case "affect_consolidation": case "affect_mode":
        S.affectStale = true;  // H7: the computed state moved; the view reloads it
        break;
      case "language_mismatch": {  // the engine wrote in another language than this life's (audit R-10)
        const names = { en: t("set.langs.en"), fr: t("set.langs.fr") };
        S.chat.push({ who: "note", text: t(d.kept_mismatch ? "lang_notice.kept" : "lang_notice.mismatch",
          { name: S.snap.name, got: names[d.got] || d.got, want: names[d.expected] || d.expected }) });
        break;
      }
      case "kernel_refusal": case "engine_error": case "engine_refusal":
        if (m) m.extras.push(d.message);
        break;
    }
    if (S.moments.length > 300) S.moments.splice(0, S.moments.length - 300);
    if (S.chat.length > 500) S.chat.splice(0, S.chat.length - 500);
    return false;
  }

  let memoryFlight = null;
  function loadMemories() {
    if (memoryFlight && memoryFlight.run === S.run) {
      memoryFlight.again = true;
      return memoryFlight.promise;
    }
    const flight = { run: S.run, again: false, headers: new Map() };
    memoryFlight = flight;
    flight.promise = (async () => {
      do {
        flight.again = false;
        flight.headers.clear();
        try {
          const data = await api("/api/memory");
          if (flight.run !== S.run) return;
          // A recall may arrive while the server's previous memory response is
          // in flight. Keep the more recent event's strength and timestamp.
          S.memories = data.memories.map((item) => ({ ...item, ...flight.headers.get(item.id) }));
          S.memLoaded = true;
          if (brain) brain.setMemories(S.memories);
          if (S.view === "memory" || S.view === "brain") refresh();
        } catch (_) { /* a later change retries */ }
      } while (flight.again && flight.run === S.run);
    })().finally(() => { if (memoryFlight === flight) memoryFlight = null; });
    return flight.promise;
  }

  async function loadDreams() {
    const run = S.run;
    try {
      const data = await api("/api/dreams");
      if (run !== S.run) return;
      S.dreams = data.dreams;
      if (S.view === "dreams") refresh();
    } catch (_) { /* next event will retry */ }
  }

  // Images are reduced in the window before they are handed over; from a video
  // only a few still frames are taken. The original file never leaves this page.
  function toJpeg(source, width, height, limit) {
    const k = Math.min(1, limit / Math.max(width, height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(width * k)); canvas.height = Math.max(1, Math.round(height * k));
    canvas.getContext("2d").drawImage(source, 0, 0, canvas.width, canvas.height);
    const url = canvas.toDataURL("image/jpeg", 0.85);
    return { media_type: "image/jpeg", data: url.slice(url.indexOf(",") + 1), url };
  }
  async function prepareImage(file) {
    let bitmap;
    try { bitmap = await createImageBitmap(file, { imageOrientation: "from-image" }); }
    catch (_) { throw new Error(t("chat.bad_image", { name: file.name })); }
    const image = toJpeg(bitmap, bitmap.width, bitmap.height, 1280);
    return { name: file.name, kind: "image", images: [{ media_type: image.media_type, data: image.data }], thumb: image.url };
  }
  function prepareVideo(file, frames) {
    return new Promise((resolve, reject) => {
      const video = document.createElement("video"), url = URL.createObjectURL(file), images = [];
      const fail = () => { URL.revokeObjectURL(url); reject(new Error(t("chat.bad_video", { name: file.name }))); };
      const timer = setTimeout(fail, 45000);
      let times = [], thumb = null;
      video.muted = true; video.preload = "auto"; video.playsInline = true;
      video.onerror = () => { clearTimeout(timer); fail(); };
      video.onloadedmetadata = () => {
        const duration = isFinite(video.duration) && video.duration > 0 ? video.duration : 0;
        if (!duration || !video.videoWidth) { clearTimeout(timer); return fail(); }
        times = Array.from({ length: frames }, (_, i) => ((i + 0.5) / frames) * duration);
        video.currentTime = times[0];
      };
      video.onseeked = () => {
        const frame = toJpeg(video, video.videoWidth, video.videoHeight, 768);
        images.push({ media_type: frame.media_type, data: frame.data, at: Math.round(times[images.length] * 10) / 10 });
        thumb = thumb || frame.url;
        if (images.length < times.length) { video.currentTime = times[images.length]; return; }
        clearTimeout(timer); URL.revokeObjectURL(url);
        resolve({ name: file.name, kind: "video", images, duration: video.duration, thumb });
      };
      video.src = url;
    });
  }
  function prepareDocument(file) {
    return new Promise((resolve, reject) => {
      if (file.size > 30e6) return reject(new Error(t("chat.too_big", { name: file.name })));
      const reader = new FileReader();
      reader.onerror = () => reject(new Error(t("errors.generic", { message: file.name })));
      reader.onload = () => resolve({ name: file.name, kind: "document", data: String(reader.result).slice(String(reader.result).indexOf(",") + 1) });
      reader.readAsDataURL(file);
    });
  }
  const mediaUrl = (id, n) => "/api/library/image?id=" + encodeURIComponent(id) + "&n=" + n + "&token=" + encodeURIComponent(TOKEN);

  // ---------- shell ----------

  const NAV = ["chat", "subconscious", "memory", "brain", "state", "affect", "milestones", "dreams", "lab", "sources", "settings"];
  let ui = {}, brain = null, view = null;

  function drawShell() {
    applyTheme();
    ui = {};
    ui.orb = h("i", { class: "orb" });
    ui.name = h("div", { class: "being-name" });
    ui.age = h("div", { class: "being-age" });
    ui.nav = h("nav", { class: "nav" }, NAV.map((id) =>
      h("button", { "data-view": id, onclick: () => go(id) }, icon(id), h("span", {}, t("nav." + id)))));
    ui.engine = h("div", { class: "engine-badge" });
    ui.title = h("h1", {});
    ui.tickerText = h("span", { class: "ticker-text" });
    ui.gauges = h("div", { class: "gauges" });
    ui.banner = h("div", { class: "banner", role: "status", hidden: true });
    ui.view = h("div", { class: "view" });
    root.replaceChildren(h("div", { class: "shell" },
      h("aside", { class: "sidebar glass" },
        brandMark(),
        h("div", { class: "being" }, ui.orb, h("div", { style: "min-width:0" }, ui.name, ui.age)),
        ui.nav,
        h("div", { class: "sidebar-foot" }, ui.engine,
          h("button", { class: "icon-btn", title: t("theme"), "aria-label": t("theme"), onclick: toggleTheme }, icon("theme")))),
      h("main", { class: "main glass" },
        h("header", { class: "main-head" }, ui.title, ui.gauges, h("div", { class: "ticker" }, ui.tickerText)),
        ui.banner, ui.view)));
    go(S.view);
  }

  function toggleTheme() {
    S.theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    store.set("fw-theme", S.theme);
    applyTheme();
    if (S.snap && ui.view && S.view === "settings") go("settings");
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
    ui.view.className = "view" + (["chat", "memory", "brain"].includes(id) ? " flush" : "") + (id === "lab" ? " wide" : "");
    ui.view.replaceChildren();
    ui.view.ondragover = ui.view.ondragleave = ui.view.ondrop = null;
    ui.view.classList.remove("dropping");
    view = VIEWS[id]();
    refresh();
  }

  function refresh() {
    const snap = S.snap;
    if (!snap || !ui.view) return;
    ui.name.textContent = snap.name;
    ui.age.textContent = t("born_ago", { age: ageOf(snap) });
    ui.engine.textContent = snap.engine.kind === "simulated" ? tr("welcome.engines").simulated[0] : (snap.engine.name || snap.engine.kind || "");
    ui.engine.title = ui.engine.textContent + (S.build ? " · Freewill " + S.build.version + (S.build.short ? " · " + S.build.short : "") : "");
    ui.tickerText.textContent = S.ticker;
    ui.banner.hidden = !snap.paused;
    ui.banner.textContent = snap.paused ? t("paused", { reason: snap.paused }) : "";
    if (typeof snap.sleeping === "boolean") S.asleep = snap.sleeping;
    ui.orb.classList.toggle("resting", S.asleep);
    if (brain) brain.setAsleep(S.asleep);
    if (window.FWLab) window.FWLab.gauges(ui.gauges, snap);
    if (view && view.update) view.update();
  }

  // ---------- views ----------

  const VIEWS = {
    lab() { return window.FWLab ? window.FWLab.view(ui.view) : {}; },
    chat() {
      const MAX = 6;
      const scroll = h("div", { class: "chat-scroll", role: "log", "aria-live": "polite" });
      const input = h("textarea", { rows: 1, "aria-label": t("chat.placeholder", { name: S.snap.name }),
                                    placeholder: t("chat.placeholder", { name: S.snap.name }) });
      const chips = h("div", { class: "chips" }), note = h("div", { class: "hint composer-note", role: "status" });
      const picker = h("input", { type: "file", multiple: true, hidden: true,
        accept: "image/*,video/*,.txt,.md,.pdf,.docx,.epub,.html,.htm,.csv,.json,.rtf,.srt,text/*" });
      let pending = [], busy = 0;
      const drawChips = () => {
        chips.replaceChildren(...pending.map((item, index) => h("span", { class: "chip" },
          item.thumb ? h("img", { src: item.thumb, alt: "" }) : icon("file"), h("span", {}, item.name),
          item.kind === "video" ? h("span", { class: "faint" }, t("chat.frames", { n: item.images.length })) : null,
          h("button", { "aria-label": t("chat.remove", { name: item.name }), onclick: () => { pending.splice(index, 1); drawChips(); } }, icon("close")))));
        const blind = !S.snap.engine.can_see && pending.some((item) => item.kind !== "document");
        if (blind) note.textContent = t("chat.blind", { name: S.snap.name });
        else if (!busy && note.dataset.kind !== "error") note.textContent = "";
      };
      const say = (text, kind) => { note.dataset.kind = kind || ""; note.textContent = text; };
      async function addFiles(files) {
        for (const file of files) {
          if (pending.length + busy >= MAX) { say(t("chat.too_many", { n: MAX }), "error"); break; }
          busy++; say(t("chat.preparing", { name: file.name }));
          try {
            const item = file.type.startsWith("image/") ? await prepareImage(file)
              : file.type.startsWith("video/") ? await prepareVideo(file, 6) : await prepareDocument(file);
            pending.push(item); say("");
          } catch (e) { say(e.message, "error"); }
          busy--; drawChips();
        }
      }
      picker.addEventListener("change", () => { addFiles([...picker.files]); picker.value = ""; });
      const send = async () => {
        const text = input.value.trim();
        if ((!text && !pending.length) || busy) return;
        const attachments = pending.map(({ thumb, ...rest }) => rest), kept = pending;
        input.value = ""; input.style.height = ""; pending = []; drawChips();
        try { await api("/api/message", { text, attachments }); say(""); }
        catch (e) { input.value = text; pending = kept; drawChips(); say(t("errors.generic", { message: e.message }), "error"); }
      };
      input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); } });
      input.addEventListener("input", () => { input.style.height = ""; input.style.height = Math.min(160, input.scrollHeight) + "px"; });
      input.addEventListener("paste", (e) => { const files = [...(e.clipboardData || {}).files || []]; if (files.length) { e.preventDefault(); addFiles(files); } });
      const zone = ui.view;
      zone.ondragover = (e) => { e.preventDefault(); zone.classList.add("dropping"); };
      zone.ondragleave = (e) => { if (!zone.contains(e.relatedTarget)) zone.classList.remove("dropping"); };
      zone.ondrop = (e) => { e.preventDefault(); zone.classList.remove("dropping"); addFiles([...e.dataTransfer.files]); };
      ui.view.append(scroll, h("div", { class: "drop-veil" }, t("chat.drop")), chips, note,
        h("div", { class: "composer" }, picker,
          h("button", { class: "icon-btn attach", title: t("chat.attach"), "aria-label": t("chat.attach"), onclick: () => picker.click() }, icon("attach")),
          input, h("button", { class: "btn primary", onclick: send }, t("chat.send"))));
      setTimeout(() => input.focus(), 0);
      const attachment = (a) => a.kind === "text"
        ? h("span", { class: "chip in" }, icon("file"), h("span", {}, a.name), h("span", { class: "faint" }, t("chat.passages", { n: a.passages })))
        : h("span", { class: "thumbs", title: a.name }, Array.from({ length: Math.min(a.frames || 1, 6) }, (_, n) =>
            h("img", { src: mediaUrl(a.id, n), alt: a.name, loading: "lazy" })));
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
                       title: m.spontaneous ? t("chat.spontaneous") : null },
              (m.attachments || []).length ? h("div", { class: "attached" }, m.attachments.map(attachment)) : null, m.text)));
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
          if (m.kind === "note") {
            return h("div", { class: "moment" + (m.past ? " past" : "") }, h("div", { class: "moment-head", style: "margin:0" },
              h("span", { class: "tag neutral" }, m.text), h("time", {}, clock(m.time))));
          }
          if (m.kind === "dream") {
            return h("article", { class: "moment dreamt" + (m.past ? " past" : "") },
              h("div", { class: "moment-head" }, h("span", { class: "tag" }, t("sub.dream")), h("b", {}, m.title), h("time", {}, clock(m.time))),
              h("div", { class: "moment-thought" }, m.text));
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
      const grid = h("div", { class: "memory" }, cols), shelf = h("div", { class: "shelf" });
      const search = h("input", { type: "search", class: "search", value: S.memQuery, placeholder: t("mem.search"), "aria-label": t("mem.search"),
        oninput: (e) => { S.memQuery = e.target.value; draw(); } });
      const tabs = h("div", { class: "tabs", role: "tablist" });
      ui.view.append(h("div", { class: "toolbar" }, tabs, search), grid, shelf);
      async function open(id) {
        S.memId = id; S.memItem = null; draw();
        try { S.memItem = await api("/api/memory/item?id=" + encodeURIComponent(id)); } catch (_) { S.memId = null; }
        draw();
      }
      function drawTabs() {
        tabs.replaceChildren(...["memories", "library"].map((id) => h("button", { role: "tab", "aria-selected": String(S.memTab === id),
          class: S.memTab === id ? "on" : "", onclick: () => { S.memTab = id; draw(); } },
          t("mem.tab_" + id), h("span", { class: "faint" }, id === "memories" ? S.memories.length : (S.snap.library || []).length))));
        const lib = S.memTab === "library";
        grid.hidden = lib; shelf.hidden = !lib; search.hidden = lib;
      }
      function drawLibrary() {
        const items = (S.snap.library || []).slice().reverse(), kinds = tr("mem.kinds");
        if (!items.length) return shelf.replaceChildren(h("div", { class: "empty" }, h("p", {}, t("mem.lib_empty", { name: S.snap.name }))));
        shelf.replaceChildren(h("p", { class: "hint", style: "margin-bottom:14px" }, t("mem.lib_hint", { name: S.snap.name })),
          ...items.map((item) => h("div", { class: "card book" },
            item.kind === "text" ? h("span", { class: "book-icon" }, icon("file")) : h("img", { src: mediaUrl(item.id, 0), alt: "" }),
            h("div", { style: "min-width:0;flex:1" },
              h("div", { class: "mem-title" }, item.name),
              h("div", { class: "small muted" }, kinds[item.kind] + " · " + day(item.added)),
              item.kind === "text"
                ? [h("div", { style: "margin:8px 0 4px" }, bar(item.read / Math.max(1, item.passages))),
                   h("div", { class: "hint" }, t("mem.lib_read", { read: item.read, of: item.passages }))]
                : h("div", { class: "hint", style: "margin-top:6px" }, t("mem.lib_frames", { n: item.frames }))))));
      }
      function draw() {
        drawTabs();
        if (S.memTab === "library") return drawLibrary();
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
        const words = S.memQuery.toLowerCase().split(/\s+/).filter(Boolean);
        const list = S.memories.filter((m) => !S.comp || m.compartment === S.comp)
          .filter((m) => { const hay = (m.title + " " + m.summary + " " + (m.tags || []).join(" ")).toLowerCase(); return words.every((w) => hay.includes(w)); })
          .sort((a, b) => (b.date || "").localeCompare(a.date || ""));
        cols[1].replaceChildren(...(list.length ? list.map((m) => h("button", { class: "mem" + (S.memId === m.id ? " active" : ""), onclick: () => open(m.id) },
          h("div", { class: "mem-title" }, m.title), h("div", { class: "mem-sum" }, m.summary),
          h("div", { class: "mem-foot" }, bar(m.strength), m.state !== "complete" ? h("span", { class: "tag neutral" }, tr("mem.states")[m.state] || m.state) : null)))
          : [h("p", { class: "muted", style: "padding:12px" }, t("mem.none"))]));
        const it = S.memItem;
        if (!it) return cols[2].replaceChildren(h("div", { class: "empty" }, h("p", {}, S.memId ? "…" : t("mem.pick"))));
        const states = tr("mem.states"), titles = new Map(S.memories.map((m) => [m.id, m.title]));
        cols[2].replaceChildren(
          h("h2", { style: "font-size:18px" }, it.title),
          h("p", { class: "muted", style: "margin-top:4px" }, it.summary),
          h("div", { class: "mem-body" }, it.body && it.body.trim() ? it.body : h("span", { class: "faint" }, t("mem.lost"))),
          h("div", { class: "kv" },
            h("b", {}, t("mem.date")), h("span", {}, day(it.date)),
            it.last_recall ? [h("b", {}, t("mem.recalled")), h("span", {}, day(it.last_recall))] : null,
            h("b", {}, t("mem.state")), h("span", {}, (states[it.state] || it.state) + (it.kept ? " · " + t("mem.kept") : "")),
            h("b", {}, t("mem.strength")), h("span", {}, pct(it.strength)),
            h("b", {}, t("mem.importance")), h("span", {}, pct(it.importance)),
            it.tags && it.tags.length ? [h("b", {}, t("mem.tags")), h("span", {}, it.tags.join(", "))] : null,
            it.affect && typeof it.affect.v === "number" ? [h("b", {}, t("mem.trace")), h("span", { title: t("mem.trace_hint") },
              t("aff.dims.valence") + " " + (it.affect.v >= 0 ? "+" : "−") + Math.abs(it.affect.v).toFixed(2) + " · " +
              t("aff.dims.arousal") + " " + Number(it.affect.a || 0).toFixed(2) + (it.affect.key ? " · " + it.affect.key : ""))] : null,
            it.links && it.links.length ? [h("b", {}, t("mem.links")), h("span", { class: "linkrow" }, it.links.filter((id) => titles.has(id)).map((id) =>
              h("button", { class: "chip in link", onclick: () => open(id) }, titles.get(id))))] : null));
      }
      if (S.memId && !S.memItem) open(S.memId);
      let shown = null, books = "";
      return { update() {
        const stamp = JSON.stringify(S.snap.library || []);
        if (shown !== S.memories || books !== stamp) { shown = S.memories; books = stamp; draw(); }
      } };
    },

    brain() {
      const canvas = h("canvas", { role: "img", "aria-label": t("brain.title"), "aria-describedby": "brain-guide", tabindex: "0" });
      const tip = h("div", { class: "brain-tip", hidden: true });
      const hud = h("div", { class: "brain-hud" }), status = h("span", { class: "brain-status", role: "status" });
      const events = h("div", { class: "brain-events", role: "log", "aria-live": "polite", "aria-label": t("brain.activity") });
      const inspector = h("div", { class: "brain-inspector" });
      const controls = h("div", { class: "brain-controls", role: "group", "aria-label": t("brain.controls") });
      let selected = null, eventStamp = null, inspectStamp = "";
      const openMemory = (id) => {
        S.memId = id; S.memItem = null; S.memTab = "memories"; S.comp = null; S.memQuery = ""; go("memory");
      };
      const drawControls = () => {
        controls.replaceChildren(...["rotate", "motion", "paused"].map((key) => {
          const on = S.brainControls[key];
          return h("button", { class: "brain-control" + (on ? " on" : ""), "aria-pressed": String(on),
            title: t("brain." + key + "_hint"), onclick: () => {
              S.brainControls[key] = !on;
              if (brain && brain.setControls) brain.setControls(S.brainControls);
              drawControls();
            } }, t("brain." + key));
        }), h("button", { class: "brain-control", title: t("brain.reset_hint"), onclick: () => { if (brain && brain.resetView) brain.resetView(); } }, t("brain.reset")));
      };
      drawControls();
      canvas.addEventListener("keydown", (event) => {
        if (event.key === "Home" || event.key === "0") {
          event.preventDefault();
          if (brain && brain.resetView) brain.resetView();
        } else if (event.key === " ") {
          event.preventDefault();
          S.brainControls.paused = !S.brainControls.paused;
          if (brain && brain.setControls) brain.setControls(S.brainControls);
          drawControls();
        }
      });
      const colors = { message: "#4fc3f7", reminiscence: "#ffb65c", question: "#c58bff", association: "#5fd6a3",
                       need: "#ff7b9c", drift: "#96a0c8", reading: "#7fd4c9", dream: "#b07cff" };
      const guide = h("details", { class: "brain-guide" }, h("summary", {}, t("brain.map_key")),
        h("div", { class: "brain-source-key" }, Object.entries(colors).map(([key, color]) =>
          h("span", {}, h("i", { style: "--source:" + color }), sourceLabel(key)))),
        h("p", { id: "brain-guide" }, t("brain.legend")));
      const observer = h("details", { class: "brain-observer", open: true },
        h("summary", {}, h("span", {}, t("brain.activity")), h("span", { class: "brain-live-label" }, t("brain.recorded"))),
        inspector, events);
      ui.view.append(h("div", { class: "brain" }, canvas,
        h("div", { class: "brain-top" }, h("div", {}, h("div", { class: "brain-eyebrow" }, t("brain.observation")),
          h("h2", {}, t("brain.title")), hud), h("div", { class: "brain-tools" }, status, controls)),
        h("div", { class: "brain-bottom" }, h("div", { class: "brain-caption" },
          h("p", {}, t("brain.hint")), guide), observer), tip));
      brain = new window.Brain(canvas, tip, { self: t("brain.self"), core: t("brain.core"), sources: tr("sources") },
        { onOpen: openMemory, onInspect: (item) => { selected = item; inspectStamp = ""; drawInspector(); } });
      brain.setMemories(S.memories);
      brain.setAsleep(S.asleep);
      if (brain.setControls) brain.setControls(S.brainControls);

      function drawInspector() {
        const memory = selected && selected.kind === "memory" ? S.memories.find((item) => item.id === selected.id) : null;
        const stamp = JSON.stringify([selected, memory, S.snap.thoughts, S.snap.weights]);
        if (stamp === inspectStamp) return;
        inspectStamp = stamp;
        if (!selected) {
          inspector.replaceChildren(h("p", { class: "brain-inspect-hint" }, t("brain.inspect_hint")));
          return;
        }
        const rows = [], item = memory || selected;
        if (selected.kind === "memory") {
          rows.push([t("mem.strength"), pct(item.strength || 0)], [t("brain.links"), (item.links || []).length]);
          if (item.compartment) rows.push([t("brain.compartment"), item.compartment]);
        } else if (selected.kind === "compartment" || selected.kind === "hub") {
          rows.push([t("brain.memories"), S.memories.filter((m) => m.compartment === selected.title).length]);
        } else if (selected.kind === "self") {
          rows.push([t("state.thoughts"), S.snap.thoughts]);
        } else {
          const source = selected.source || String(selected.id || "").replace(/^~/, "");
          const weight = S.snap.weights[source];
          if (typeof weight === "number") rows.push([t("brain.weight"), "× " + weight.toFixed(2)]);
          rows.push([t("brain.zone"), sourceLabel(source)]);
        }
        inspector.replaceChildren(h("div", { class: "brain-inspect-title" },
          h("b", {}, selected.title), h("span", { class: "tag neutral" }, t("brain.kinds." + selected.kind))),
          h("dl", {}, rows.map(([key, value]) => [h("dt", {}, key), h("dd", {}, value)]).flat()),
          selected.kind === "memory" ? h("button", { class: "brain-control", onclick: () => openMemory(selected.id) }, t("brain.open_memory")) : null);
      }

      function drawEvents() {
        const stamp = S.brainActivity.map((e) => e.seq).join(":");
        if (stamp === eventStamp) return;
        eventStamp = stamp;
        const list = S.brainActivity.slice(-4).reverse();
        if (!list.length) {
          events.replaceChildren(h("p", { class: "brain-inspect-hint" }, t("brain.no_events")));
          return;
        }
        events.replaceChildren(...list.map((event) => {
          const d = event.data || {};
          let label = t("brain.events." + event.type);
          if (event.type === "stage") label += " · " + sourceLabel(d.source);
          if (event.type === "decision") label += " · " + (d.accepted ? t("sub.welcomed") : t("sub.dismissed"));
          if (event.type === "recall" && d.phase === "dream") label += " · " + t("sub.dream");
          const text = d.title || d.thought || d.text || d.name || d.reason || d.message || "";
          return h("div", { class: "brain-event" + (event.past ? " past" : ""), "data-event": event.type },
            h("div", {}, h("b", {}, label), h("time", {}, event.past ? t("brain.history") : clock(event.time))),
            text ? h("p", { title: text }, text) : null);
        }));
      }

      return { update() {
        brain.setNeeds(S.snap.needs);
        if (brain.setSnapshot) brain.setSnapshot(S.snap);
        if (brain.setPaused) brain.setPaused(S.snap.paused);
        const activity = S.snap.activity || (S.asleep ? "sleeping" : S.snap.paused ? "paused" : "waiting");
        status.dataset.activity = activity;
        status.textContent = t("brain.states." + activity);
        status.title = S.snap.paused || t("brain.states." + activity);
        const counts = brain.counts || { memories: 0, links: 0 };
        hud.replaceChildren(
          h("span", {}, h("b", {}, counts.memories), " " + t("brain.memories")),
          h("span", {}, h("b", {}, counts.links), " " + t("brain.memory_links")),
          h("span", {}, h("b", {}, S.snap.thoughts), " " + t("brain.thoughts")));
        drawInspector(); drawEvents();
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

    // H7. An observation panel for a computed state: numbers, curves, causes. Nothing here
    // says or suggests that anything is felt.
    affect() {
      const box = h("div", { class: "affect" });
      ui.view.append(box);
      let loading = false, last = 0, error = "";
      const DIMS = ["valence", "arousal", "uncertainty", "control", "coherence", "regulatory_load", "social_context"];
      const CURVES = [["valence", "var(--accent)"], ["arousal", "var(--good)"], ["uncertainty", "var(--warn, #c98a1b)"]];
      const unit = (name, v) => (name === "valence" ? (v + 1) / 2 : v);
      const signed = (name, v) => (name === "valence" ? (v >= 0 ? "+" : "−") + Math.abs(v).toFixed(2) : v.toFixed(2));
      async function load() {
        if (loading) return;
        loading = true; S.affectStale = false; last = Date.now();
        try { S.affect = await api("/api/affect"); error = ""; } catch (e) { error = e.message; S.affectStale = true; }
        loading = false; draw();
      }
      async function toggle(enabled) {
        try { S.affect = await api("/api/affect", { enabled }); error = ""; } catch (e) { error = e.message; }
        draw();
      }
      function chart(history) {
        const W = 640, H = 150, n = history.length, wrap = h("div", { class: "affect-chart", role: "img", "aria-label": t("aff.curves_alt") });
        if (n < 2) { wrap.append(h("p", { class: "hint" }, t("aff.no_history"))); return wrap; }
        const x = (i) => (i / (n - 1)) * W, y = (u) => H - 6 - u * (H - 12);
        const lines = CURVES.map(([name, color]) => '<polyline fill="none" stroke="' + color + '" stroke-width="1.8" stroke-linejoin="round" points="' +
          history.map((p, i) => x(i).toFixed(1) + "," + y(unit(name, Number(p[name]) || 0)).toFixed(1)).join(" ") + '"/>').join("");
        // Numbers only: nothing coming from the being or the person is put in this markup.
        wrap.innerHTML = '<svg viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="none" aria-hidden="true">' +
          '<line x1="0" x2="' + W + '" y1="' + y(0.5) + '" y2="' + y(0.5) + '" stroke="currentColor" opacity=".18" stroke-dasharray="3 4"/>' + lines + "</svg>";
        wrap.append(h("div", { class: "affect-legend" }, CURVES.map(([name, color]) =>
          h("span", {}, h("i", { style: "background:" + color }), t("aff.dims." + name)))));
        return wrap;
      }
      function draw() {
        const a = S.affect;
        if (!a) return box.replaceChildren(h("p", { class: "hint" }, error ? t("errors.generic", { message: error }) : "…"));
        const head = h("section", { class: "card affect-head" },
          h("div", { style: "flex:1;min-width:0" },
            h("div", { class: "section-title" }, t("aff.title")),
            h("p", {}, t("aff.caveat")),
            h("p", { class: "hint", style: "margin-top:8px" }, a.enabled ? t("aff.on_hint", { name: S.snap.name }) : t("aff.off_hint", { name: S.snap.name }))),
          h("button", { class: "switch" + (a.enabled ? " on" : ""), role: "switch", "aria-checked": String(a.enabled),
            "aria-label": t("aff.switch"), onclick: () => toggle(!a.enabled) }, h("i", {}), h("span", {}, a.enabled ? t("aff.on") : t("aff.off"))));
        if (!a.enabled && !a.exists) return box.replaceChildren(...[head, error ? h("p", { class: "error" }, error) : null].filter(Boolean));
        const v = a.state.values, traced = S.memories.filter((m) => m.affect && typeof m.affect.v === "number");
        const cons = a.last_consolidation;
        box.replaceChildren(...[head,
          error ? h("p", { class: "error", role: "alert" }, error) : null,
          a.recovered ? h("p", { class: "error", role: "alert" }, t("aff.recovered_" + a.recovered)) : null,
          h("div", { class: "grid-2" },
            h("section", { class: "card" }, h("div", { class: "section-title" }, t("aff.levels")),
              DIMS.map((name) => h("div", { class: "meter affect-meter", title: t("aff.help." + name) },
                h("span", {}, t("aff.dims." + name)),
                h("div", { class: "bar" }, h("i", { style: "width:" + Math.round(100 * unit(name, v[name])) + "%" }),
                  h("b", { class: "setpoint", style: "left:" + Math.round(100 * unit(name, a.setpoints[name])) + "%", title: t("aff.rest") })),
                h("span", {}, signed(name, v[name])))),
              h("p", { class: "hint", style: "margin-top:10px" }, t("aff.levels_hint"))),
            h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("aff.curves")), chart(a.history)),
            h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("aff.triggers")),
              a.recent.length ? a.recent.slice().reverse().slice(0, 8).map((r) => h("div", { class: "trigger" },
                h("div", { class: "moment-head" }, h("span", { class: "tag neutral" }, r.key), h("span", { class: "small muted" }, t("aff.kinds." + r.kind)),
                  h("span", { class: "small faint" }, "Δ " + Number(r.delta).toFixed(2)), h("time", {}, clock(r.time))),
                h("ul", { class: "causes" }, r.causes.map((c) => h("li", {}, c)))))
                : h("p", { class: "muted" }, t("aff.no_triggers"))),
            h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("aff.learned")),
              a.associations.length ? a.associations.map((x) => h("div", { class: "meter affect-meter" },
                h("span", { title: x.key }, x.key), h("div", { class: "bar" }, h("i", { style: "width:" + Math.round(100 * unit("valence", x.valence)) + "%" }),
                  h("b", { class: "setpoint", style: "left:50%" })), h("span", {}, signed("valence", x.valence) + " · " + x.n)))
                : h("p", { class: "muted" }, t("aff.no_learned")),
              h("p", { class: "hint", style: "margin-top:10px" }, t("aff.learned_hint", { n: a.episodes }))),
            h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("aff.sleep")),
              cons ? [h("div", { class: "kv", style: "margin-top:0" },
                  h("b", {}, t("aff.when")), h("span", {}, day(cons.time)),
                  h("b", {}, t("aff.episodes")), h("span", {}, cons.episodes + " · " + cons.contexts + " " + t("aff.contexts")),
                  cons.skipped ? [h("b", {}, t("aff.gap")), h("span", {}, t("aff.skipped"))]
                    : [h("b", {}, t("aff.gap")), h("span", {}, Number(cons.error_before).toFixed(3) + " → " + Number(cons.error_after).toFixed(3))],
                  h("b", {}, t("aff.dims.valence")), h("span", {}, signed("valence", cons.state_before.valence) + " → " + signed("valence", cons.state_after.valence)),
                  h("b", {}, t("aff.dims.regulatory_load")), h("span", {}, cons.state_before.regulatory_load.toFixed(2) + " → " + cons.state_after.regulatory_load.toFixed(2))),
                h("p", { class: "hint", style: "margin-top:10px" }, t("aff.sleep_hint"))]
                : h("p", { class: "muted" }, t("aff.no_sleep"))),
            h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("aff.memory")),
              h("p", {}, t("aff.memory_text", { n: traced.length, of: S.memories.length })),
              traced.length ? h("div", { class: "linkrow", style: "margin-top:10px" }, traced.slice(-8).reverse().map((m) =>
                h("button", { class: "chip in link", title: t("aff.dims.valence") + " " + signed("valence", m.affect.v),
                  onclick: () => { S.memId = m.id; S.memItem = null; S.memTab = "memories"; S.comp = null; S.memQuery = ""; go("memory"); } }, m.title))) : null,
              h("p", { class: "hint", style: "margin-top:10px" }, t("aff.rules", { rules: a.rules }))))].filter(Boolean));
      }
      draw();
      return { update() { if (S.affectStale && Date.now() - last > 900) load(); } };
    },

    milestones() {
      let shown = "";
      return { update() {
        const snap = S.snap, stamp = JSON.stringify(snap.milestones);
        if (stamp === shown) return;
        shown = stamp;
        const order = ["first_thought", "first_refusal", "first_memory", "first_spontaneous_word", "first_silence", "first_value", "first_dream"];
        const done = order.filter((k) => snap.milestones[k]).sort((a, b) => snap.milestones[a].localeCompare(snap.milestones[b]));
        ui.view.replaceChildren(h("div", { class: "timeline" },
          h("div", { class: "tl" }, h("b", {}, t("miles.birth")), h("span", { class: "small muted" }, day(snap.born))),
          done.map((k) => h("div", { class: "tl" }, h("b", {}, t("miles." + k)), h("span", { class: "small muted" }, day(snap.milestones[k])))),
          order.filter((k) => !snap.milestones[k]).map((k) =>
            h("div", { class: "tl pending" }, h("b", {}, t("miles." + k)), h("span", { class: "small" }, t("miles.not_yet"))))));
      } };
    },

    dreams() {
      const list = h("div", { class: "dreams" });
      const button = h("button", { class: "btn", onclick: async () => { button.disabled = true; try { await api("/api/sleep", {}); } catch (_) { button.disabled = false; } } });
      ui.view.append(h("div", { class: "toolbar plain" }, h("p", { class: "hint", style: "flex:1" }, t("dreams.hint")), button), list);
      if (!S.dreams) loadDreams();
      let shown;
      return { update() {
        button.textContent = S.asleep ? t("dreams.sleeping", { name: S.snap.name }) : t("dreams.sleep");
        if (S.asleep) button.disabled = true; else if (shown !== undefined && !S.asleep) button.disabled = false;
        if (shown === S.dreams && shown !== undefined) return;
        shown = S.dreams;
        if (!S.dreams) return list.replaceChildren(h("div", { class: "empty" }, h("p", {}, "…")));
        if (!S.dreams.length) return list.replaceChildren(h("div", { class: "empty" }, h("p", {}, t("dreams.empty", { name: S.snap.name }))));
        const known = new Set(S.memories.map((m) => m.id));
        list.replaceChildren(...S.dreams.map((d) => h("article", { class: "card dream" },
          h("div", { class: "moment-head" }, h("h2", {}, d.title), h("time", {}, day(d.date))),
          h("p", { class: "dream-text" }, d.text),
          d.residue ? h("p", { class: "dream-residue" }, h("b", {}, t("dreams.residue") + " : "), d.residue) : null,
          (d.memories || []).length ? h("div", { class: "linkrow", style: "margin-top:12px" }, h("span", { class: "hint" }, t("dreams.woven")),
            d.memories.map((m) => h("button", { class: "chip in link", disabled: !known.has(m.id),
              onclick: () => { S.memId = m.id; S.memItem = null; S.memTab = "memories"; S.comp = null; S.memQuery = ""; go("memory"); } }, m.title))) : null)));
      } };
    },

    sources() {
      const box = h("div", { class: "sources" }, h("p", { class: "hint" }, "…"));
      ui.view.append(box);
      api("/api/credits").then((data) => {
        const item = (name, role, author, licence, licenceUrl, url, extra) => h("div", { class: "card source" },
          h("div", { class: "model-head" }, h("b", {}, name), extra || null),
          role ? h("div", { class: "small muted" }, role) : null,
          h("div", { class: "model-src" }, h("span", {}, author),
            licence ? (licenceUrl ? link(licenceUrl, licence) : h("span", {}, licence)) : null, link(url, t("models.source"))));
        box.replaceChildren(
          h("p", { class: "lead" }, t("src.lead")),
          h("div", { class: "section-title" }, t("src.models")),
          h("p", { class: "hint", style: "margin-bottom:10px" }, t("src.models_hint")),
          ...data.models.map((m) => item(m.name, t("models.needs", { size: gb(m.download_size), ram: m.ram_gb }), m.author, m.licence, m.licence_url, m.source_url,
            [h("span", { class: "tag neutral" }, t("models.tiers." + m.tier)), m.installed ? h("span", { class: "tag good" }, t("models.installed")) : null])),
          h("div", { class: "section-title", style: "margin-top:26px" }, t("src.software")),
          ...data.software.map((s) => item(s.name, s.role[S.lang] || s.role.en, s.author, s.licence, null, s.url)),
          h("div", { class: "section-title", style: "margin-top:26px" }, t("src.research")),
          h("div", { class: "card source" }, h("p", { class: "small muted" }, t("src.research_text")),
            h("div", { class: "model-src" }, link(data.project + "#readme", t("src.readme")), link(data.project, t("src.project")))));
      }).catch((e) => box.replaceChildren(h("p", { class: "error" }, t("errors.generic", { message: e.message }))));
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
      // Another engine for the same being: its life file, and so itself, does not change.
      const changer = h("div", { class: "changer" });
      const C = { open: false, kind, model: snap.engine.model || "", key: "", error: "", busy: false };
      function drawChanger() {
        if (!C.open) return changer.replaceChildren(h("button", { class: "btn", style: "margin-bottom:14px", onclick: () => { C.open = true; drawChanger(); } }, t("set.change")));
        const kinds = ["embedded", "local", "anthropic", "openai", "xai", "simulated"];
        const needsKey = ["anthropic", "openai", "xai"].includes(C.kind);
        fill(changer,
          h("p", { class: "hint", style: "margin-bottom:10px" }, t("set.change_hint", { name: snap.name })),
          h("div", { class: "field" }, h("label", { for: "c-kind" }, t("set.engine")),
            select("c-kind", C.kind, kinds.map((k) => [k, tr("welcome.engines")[k][0]]), (v) => { C.kind = v; C.model = ""; C.error = ""; drawChanger(); })),
          C.kind === "embedded" ? modelPicker(C.model, (id) => { C.model = id; }, kind === "embedded" ? snap.engine.model : null) : null,
          C.kind !== "embedded" && C.kind !== "simulated" ? h("div", { class: "field" }, h("label", { for: "c-model" }, t("welcome.model")),
            h("input", { id: "c-model", value: C.model, autocomplete: "off", spellcheck: "false", oninput: (e) => { C.model = e.target.value; } })) : null,
          needsKey ? h("div", { class: "field" }, h("label", { for: "c-key" }, t("set.key")),
            h("input", { id: "c-key", type: "password", autocomplete: "off", placeholder: S.keys[C.kind] ? "••••••••" : "", oninput: (e) => { C.key = e.target.value; } }),
            h("span", { class: "hint" }, S.keys[C.kind] ? t("set.key_set") : t("set.key_hint"))) : null,
          C.error ? h("div", { class: "error", role: "alert" }, C.error) : null,
          h("div", { class: "actions", style: "margin:12px 0 16px" },
            h("button", { class: "btn", onclick: () => { C.open = false; C.error = ""; drawChanger(); } }, t("welcome.back")),
            h("button", { class: "btn primary", disabled: C.busy, onclick: async () => {
              if (C.kind === "embedded" && !C.model) { C.error = t("models.pick_first"); return drawChanger(); }
              C.busy = true; drawChanger();
              const engine = { kind: C.kind };
              if (C.model.trim()) engine.model = C.model.trim();
              try {
                const next = await api("/api/engine", { engine, api_key: C.key.trim() || undefined });
                enter(next);
              } catch (e) { C.busy = false; C.error = t("errors.generic", { message: e.message }); drawChanger(); }
            } }, t("set.apply"))));
      }
      drawChanger();
      ui.view.append(h("div", { class: "grid-2" },
        h("section", { class: "card" }, h("div", { class: "section-title" }, t("set.appearance")),
          h("div", { class: "field" }, h("label", { for: "s-theme" }, t("set.theme")),
            select("s-theme", S.theme, [["system", t("set.system")], ["light", t("set.light")], ["dark", t("set.dark")]],
              (v) => { S.theme = v; store.set("fw-theme", v); applyTheme(); })),
          h("div", { class: "field" }, h("label", { for: "s-lang" }, t("set.language")),
            select("s-lang", S.lang, [["fr", "Français"], ["en", "English"]],
              (v) => { S.lang = v; store.set("fw-lang", v); drawShell(); })),
          h("div", { class: "field" }, h("label", {}, t("set.life_language", { name: snap.name })),
            h("p", {}, t("set.langs." + (snap.language === "fr" ? "fr" : "en"))),
            h("span", { class: "hint" }, t("set.life_language_hint", { name: snap.name, lang: t("set.langs." + (snap.language === "fr" ? "fr" : "en")) })))),
        h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("set.rhythm")),
          h("div", { class: "row" },
            h("div", { class: "field" }, h("label", { for: "s-tempo" }, t("set.tempo")), number("s-tempo", snap.tempo, 2, 3600, "tempo")),
            h("div", { class: "field" }, h("label", { for: "s-hour" }, t("set.per_hour")), number("s-hour", snap.thoughts_per_hour, 0, 3600, "thoughts_per_hour"))),
          h("p", { class: "hint" }, t("set.rhythm_hint")), saved),
        h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, t("set.engine")),
          h("p", { style: "margin-bottom:12px" }, snap.engine.name || kind),
          changer,
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
      const about = h("section", { class: "card about-build" }, h("div", { class: "section-title" }, t("about.title")), h("p", { class: "muted" }, "…"));
      ui.view.append(about);
      api("/api/about").then((data) => drawAbout(about, data)).catch((e) => about.append(h("p", { class: "error" }, t("errors.generic", { message: e.message }))));
      const research = h("div", { class: "research-settings" });
      ui.view.append(research);
      if (window.FWLab) window.FWLab.settings(research);
      return {};
    },
  };

  // Which code runs, and what can really learn: never a setting shown as a validated training (audit R-09, 9.1).
  function drawAbout(box, data) {
    const b = data.build, unknown = t("about.unknown");
    const row = (label, value) => h("div", { class: "about-row" }, h("span", { class: "muted" }, label), h("span", {}, value));
    const engine = data.engine;
    fill(box, h("div", { class: "section-title" }, t("about.title")),
      row(t("about.version"), b.version + (b.tag ? " (" + b.tag + ")" : "")),
      row(t("about.commit"), h("code", { title: b.commit || "" }, b.short || unknown)),
      b.dirty ? h("p", { class: "hint" }, t("about.dirty")) : null,
      b.tag_matches === false ? h("p", { class: "error" }, t("about.tag_mismatch", { tag: b.tag })) : null,
      row(t("about.built"), b.built_utc ? new Date(b.built_utc).toLocaleString(S.lang) : unknown),
      row(t("about.channel"), t("about.channels." + (b.channel === "installer" ? "installer" : "source"))),
      engine ? row(t("about.engine"), (engine.name || engine.kind) + " · " + (engine.can_learn ? t("about.learns") : t("about.frozen"))
        + (engine.adapter ? " · " + t("about.adapter", { v: engine.adapter }) : "")) : null,
      h("div", { class: "section-title", style: "margin-top:14px" }, t("about.caps")),
      h("table", { class: "about-caps" }, h("tbody", {}, data.capabilities.map((c) => h("tr", {},
        h("td", {}, t("about.ids." + c.id)),
        h("td", {}, h("span", { class: "state-pill " + c.state }, t("about.states." + c.state))),
        h("td", { class: "small muted" }, [t("about.reasons." + c.reason), t("about.evidence." + c.evidence)].filter(Boolean).join(" · ")))))),
      h("p", { class: "hint", style: "margin-top:8px" }, t("about.caps_hint")),
      data.untested.length ? h("p", { class: "hint" }, t("about.untested", { list: data.untested.map((k) => t("about.untested_items." + k)).join(", ") })) : null);
  }

  // What the Research Lab's own file builds on.
  window.FW = { S, h, t, tr, api, bar, pct, icon, link, store, go: (id) => go(id), refresh: () => refresh(),
                absorbSnap: (snap) => { S.snap = snap; refresh(); } };

  // ---------- start ----------

  applyTheme();
  (async function start() {
    try {
      const consent = await api("/api/consent");
      if (!consent.accepted) return showGate(consent);
      const info = await api("/api/lives");
      S.keys = info.keys || {};
      S.build = info.build || null;
      if (info.awake) return enter(await api("/api/snapshot"));
    } catch (_) { /* fall through to the welcome screen */ }
    showWelcome();
  })();
})();
