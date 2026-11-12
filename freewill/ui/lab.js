// Freewill Research Lab, research settings and header gauges.
// Every figure shown here was computed by the service; this file only displays it.
// No sentence a person reads is written here: all of them come from the fr and en catalogues.
(function () {
  "use strict";
  const { S, h, t, tr, api, bar, store } = window.FW;
  const L = { tab: "home", home: null, exp: null, expData: null, obs: null, obsData: null, reports: null,
              learning: null, engine: null, models: null, engDraft: null, error: "", busy: false, blind: false, timer: null };

  const num = (x, d) => (x == null ? t("lab.na") : Number(x).toLocaleString(S.lang, { maximumFractionDigits: d == null ? 4 : d }));
  const signed = (x) => (x == null ? t("lab.na") : (x >= 0 ? "+" : "−") + Math.abs(x).toLocaleString(S.lang, { maximumFractionDigits: 4 }));
  const when = (iso) => { try { return new Date(iso).toLocaleString(S.lang, { dateStyle: "medium", timeStyle: "short" }); } catch (_) { return iso; } };
  const range = (i) => (i ? "[" + signed(i[0]) + " ; " + signed(i[1]) + "]" : t("lab.na"));
  const code = (msg) => { const known = tr("lab.codes") || {}; return known[msg] || (/^http_\d+$/.test(msg) ? t("lab.codes.http", { status: msg.slice(5) }) : msg); };
  const tag = (label, kind) => h("span", { class: "tag " + (kind || "neutral") }, label);
  const field = (label, control, hint) => h("div", { class: "field" }, h("label", {}, label), control, hint ? h("span", { class: "hint" }, hint) : null);
  const select = (value, options, onchange) => h("select", { onchange: (e) => onchange(e.target.value) },
    options.map(([v, label]) => h("option", { value: v, selected: v === value }, label)));
  const table = (head, rows) => h("div", { class: "table-wrap" }, h("table", { class: "table" },
    h("thead", {}, h("tr", {}, head.map((c) => h("th", {}, c)))), h("tbody", {}, rows.map((r) => h("tr", {}, r.map((c) => h("td", {}, c)))))));

  async function call(path, body) {
    L.error = "";
    try { return await api(path, body); } catch (e) { L.error = code(e.message); return null; }
  }

  // ---------- header gauges: computed variables, read from the snapshot ----------

  function gauges(box, snap) {
    if (!box) return;
    if (store.get("fw-gauges", "on") !== "on" || !snap) { box.replaceChildren(); box.hidden = true; return; }
    box.hidden = false;
    const names = tr("state.names") || {}, dims = tr("aff.dims") || {}, help = tr("aff.help") || {};
    const items = ["curiosity", "wonder", "company", "fatigue"].map((k) => [names[k] || k, snap.needs[k], t("lab.gauge_need"), false]);
    const state = snap.affect && snap.affect.enabled && snap.affect.state;
    if (state) for (const k of ["valence", "arousal", "uncertainty"]) items.push([dims[k], k === "valence" ? (state[k] + 1) / 2 : state[k], help[k], k === "valence"]);
    box.title = t("lab.gauge_caveat");
    box.replaceChildren(...items.map(([label, value, hint, centred]) => h("div", { class: "gauge" + (centred ? " centred" : ""), title: hint + " · " + t("lab.gauge_caveat") },
      h("span", {}, label), bar(value == null ? 0 : value))));
  }

  // ---------- research settings: each switch is one mechanism of the life loop ----------

  // Freewill's own model: the ceiling the person chooses, and what each size asks of a computer.
  function ownCapacityCard(own, choose, saveCeiling) {
    const k = (name, vars) => t("own.cap." + name, vars);
    if (!own) return h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, k("title")), h("p", { class: "hint" }, "…"));
    const billions = (n) => (n / 1e9).toLocaleString(S.lang, { maximumFractionDigits: 2 }) + " " + k("billion");
    const gb = (x) => num(x, x < 10 ? 1 : 0) + " " + t("models.gb");
    const days = (d) => d >= 365 ? k("years", { n: num(d / 365, 1) }) : d >= 1 ? k("days", { n: num(d, 1) }) : k("hours", { n: num(d * 24, 1) });
    const chosen = own.target || own.settings.max_parameters;
    const row = own.sizes.find((r) => r.target === chosen) || own.sizes[own.sizes.length - 1];
    const fit = (v) => v == null ? tag(k("unknown")) : tag(v ? k("yes") : k("no"), v ? "good" : "bad");
    const m = own.machine;
    const options = own.presets.map((p) => [String(p), billions(p)]);
    if (!own.presets.includes(chosen)) options.push([String(chosen), billions(chosen)]);
    const custom = h("input", { type: "number", min: own.present.parameters / 1e9, step: 0.5, value: chosen / 1e9, "aria-label": k("custom") });
    return h("section", { class: "card", style: "margin-top:0" },
      h("div", { class: "section-title" }, k("title")),
      h("p", { class: "hint", style: "margin-bottom:10px" }, k("lead")),
      h("div", { class: "kv" }, h("b", {}, k("present")), h("span", {}, num(own.present.parameters, 0) + (own.present.checkpoint ? " · " + own.present.checkpoint : " · " + k("at_birth"))),
        h("b", {}, k("ceiling")), h("span", {}, num(own.settings.max_parameters, 0) + (own.settings.set_by ? " · " + own.settings.set_by : ""))),
      h("div", { class: "row", style: "margin-top:12px" },
        h("div", { class: "field" }, h("label", {}, k("choose")), select(String(chosen), options, (v) => choose(Number(v)))),
        h("div", { class: "field" }, h("label", {}, k("custom")), custom),
        h("div", { class: "btn-row" }, h("button", { class: "btn", onclick: () => choose(Math.round(Number(custom.value) * 1e9)) }, k("see")),
          h("button", { class: "btn primary", disabled: chosen === own.settings.max_parameters, onclick: () => saveCeiling(chosen) }, k("save")))),
      h("div", { class: "section-title", style: "margin-top:16px" }, k("needs", { size: billions(row.target) })),
      table([k("col_what"), k("col_need"), k("col_here")], [
        [k("disk"), gb(row.disk_gb) + " (" + k("ssd") + ")", fit(row.fits_here.store)],
        [k("run"), k("run_line", { bf16: gb(row.run_memory_gb.bf16), int8: gb(row.run_memory_gb.int8), q4: gb(row.run_memory_gb.q4) }), fit(row.fits_here.run)],
        [k("run_gpu"), (row.run_gpu.count > 1 ? row.run_gpu.count + " × " : "") + gb(row.run_gpu.memory_gb), ""],
        [k("train_frozen"), gb(row.train_frozen_base_gb), fit(row.fits_here.train_frozen_base)],
        [k("train_all"), gb(row.train_everything_gb), ""],
        [k("cpu"), k("cores", { n: row.cpu_cores_advised }), m.cpu_cores ? k("cores", { n: m.cpu_cores }) : ""],
        [k("text"), k("text_line", { tokens: num(row.tokens_needed / 1e9, 1), books: num(row.books_needed, 0) }), ""]]),
      h("div", { class: "section-title", style: "margin-top:16px" }, k("time_title", { n: num(row.new_parameters, 0) })),
      table([k("col_device"), k("col_count"), k("col_time")], row.training_time.map((d) => [k("devices." + d.device), num(d.count, 0), row.new_parameters ? days(d.days) : "—"])),
      h("div", { class: "section-title", style: "margin-top:16px" }, k("here")),
      h("div", { class: "kv" }, h("b", {}, k("cpu")), h("span", {}, m.cpu_cores ? k("cores", { n: m.cpu_cores }) : t("lab.na")),
        h("b", {}, k("ram")), h("span", {}, m.ram_gb == null ? t("lab.na") : gb(m.ram_gb)),
        h("b", {}, k("free_disk")), h("span", {}, m.disk_free_gb == null ? t("lab.na") : gb(m.disk_free_gb)),
        h("b", {}, "GPU"), h("span", {}, m.gpus.length ? m.gpus.map((g) => g.name + " · " + gb(g.memory_gb)).join(", ") : k("no_gpu"))),
      h("p", { class: "hint", style: "margin-top:10px" }, k("caveat")));
  }

  function settings(box) {
    let data = null, affect = null, exported = null, own = null;
    const draw = () => {
      if (!data) return box.replaceChildren(h("p", { class: "hint" }, "…"));
      const names = tr("rs.names"), hints = tr("rs.hints"), groups = tr("rs.groups");
      const changed = Object.keys(data.changed).length;
      const control = (item) => {
        const value = data.values[item.name];
        if (item.kind === "switch") return h("button", { class: "switch" + (value ? " on" : ""), role: "switch", "aria-checked": String(value),
          onclick: () => save({ [item.name]: !value }) }, h("i", {}), h("span", {}, value ? t("rs.on") : t("rs.off")));
        return h("input", { type: "number", min: item.min, max: item.max, step: item.whole ? 1 : 0.01, value,
          "aria-label": names[item.name], onchange: (e) => save({ [item.name]: Number(e.target.value) }) });
      };
      const row = (item) => h("div", { class: "setting" + (item.name in data.changed ? " changed" : "") },
        h("div", {}, h("b", {}, names[item.name]), h("div", { class: "hint" }, hints[item.name])), control(item));
      const group = (id) => h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, groups[id]),
        data.spec.filter((i) => i.group === id).map(row));
      const cards = ["subconscious", "memory", "sleep", "expression", "modules"].map(group);
      if (affect) {
        const an = tr("rs.affect_names"), cfg = affect.config;
        const arow = (name) => h("div", { class: "setting" }, h("div", {}, h("b", {}, an[name])),
          typeof cfg[name] === "boolean"
            ? h("button", { class: "switch" + (cfg[name] ? " on" : ""), role: "switch", "aria-checked": String(cfg[name]), disabled: !affect.enabled,
                onclick: () => saveAffect({ config: { [name]: !cfg[name] } }) }, h("i", {}), h("span", {}, cfg[name] ? t("rs.on") : t("rs.off")))
            : h("input", { type: "number", step: "any", value: cfg[name], disabled: !affect.enabled, "aria-label": an[name],
                onchange: (e) => saveAffect({ config: { [name]: Number(e.target.value) } }) }));
        cards.push(h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, groups.affect),
          h("div", { class: "setting" }, h("div", {}, h("b", {}, t("aff.switch")), h("div", { class: "hint" }, t("rs.affect_hint"))),
            h("button", { class: "switch" + (affect.enabled ? " on" : ""), role: "switch", "aria-checked": String(affect.enabled),
              onclick: () => saveAffect({ enabled: !affect.enabled }) }, h("i", {}), h("span", {}, affect.enabled ? t("rs.on") : t("rs.off")))),
          Object.keys(cfg).filter((k) => an[k]).map(arow)));
      }
      cards.push(ownCapacityCard(own, chooseOwn, saveOwn));
      cards.push(h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, groups.display),
        h("div", { class: "setting" }, h("div", {}, h("b", {}, t("rs.gauges")), h("div", { class: "hint" }, t("lab.gauge_caveat"))),
          h("button", { class: "switch" + (store.get("fw-gauges", "on") === "on" ? " on" : ""), role: "switch",
            onclick: () => { store.set("fw-gauges", store.get("fw-gauges", "on") === "on" ? "off" : "on"); window.FW.refresh(); draw(); } },
            h("i", {}), h("span", {}, store.get("fw-gauges", "on") === "on" ? t("rs.on") : t("rs.off"))))));
      cards.push(h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, groups.data),
        h("p", { class: "hint", style: "margin-bottom:10px" }, t("rs.export_hint")),
        h("div", { class: "btn-row" },
          h("button", { class: "btn", onclick: () => doExport(false) }, t("rs.export")),
          h("button", { class: "btn", onclick: () => doExport(true) }, t("rs.export_words")),
          h("button", { class: "btn", onclick: () => call("/api/export/reveal", {}) }, t("rs.reveal"))),
        exported ? h("p", { class: "small muted", style: "margin-top:10px" }, t("rs.exported", { path: exported.path })) : null));
      cards.push(h("section", { class: "card", style: "margin-top:0" }, h("div", { class: "section-title" }, groups.kernel),
        h("p", { class: "small" }, t("rs.kernel_text")),
        h("p", { class: "hint", style: "margin-top:8px" }, t("state.kernel") + " : " + S.snap.kernel)));
      box.replaceChildren(...[
        h("div", { class: "research-head" }, h("div", {}, h("h2", {}, t("rs.title")), h("p", { class: "hint" }, t("rs.lead"))),
          h("div", { class: "btn-row" }, tag(changed ? t("rs.changed", { n: changed }) : t("rs.default"), changed ? "bad" : "good"),
            h("button", { class: "btn", disabled: !changed, onclick: () => save(null, true) }, t("rs.reset")))),
        L.error ? h("div", { class: "error", role: "alert" }, L.error) : null,
        data.recovered ? h("p", { class: "error" }, t("rs.recovered")) : null,
        h("div", { class: "grid-2" }, cards)].filter(Boolean));
    };
    async function save(changes, reset) {
      const next = await call("/api/research", reset ? { reset: true } : { changes });
      if (next) data = next;
      draw();
    }
    async function saveAffect(body) {
      const next = await call("/api/affect", body);
      if (next) { affect = next; S.affect = next; }
      draw();
    }
    async function doExport(content) { exported = await call("/api/export", { content }) || exported; draw(); }
    async function chooseOwn(target) {
      if (!target || !isFinite(target)) return;
      const next = await call("/api/own-model?target=" + target);
      if (next) { own = next; own.target = target; }
      draw();
    }
    async function saveOwn(target) {
      const next = await call("/api/own-model/settings", { max_parameters: target });
      if (next) own = next;
      draw();
    }
    draw();
    Promise.all([call("/api/research"), call("/api/affect"), call("/api/own-model")]).then(([r, a, o]) => { data = r; affect = a; own = o; draw(); });
  }

  // ---------- the lab ----------

  function view(root) {
    const box = h("div", { class: "lab" });
    root.append(box);
    const TABS = ["home", "hypotheses", "experiments", "observers", "reports", "model"];

    async function load() {
      L.home = await call("/api/lab/home?lang=" + S.lang) || L.home;
      if (L.exp) L.expData = await call("/api/lab/experiment?id=" + encodeURIComponent(L.exp)) || L.expData;
      if (L.obs) L.obsData = await call("/api/lab/observer?id=" + encodeURIComponent(L.obs)) || L.obsData;
      if (L.tab === "reports") L.reports = (await call("/api/lab/reports") || {}).reports || L.reports;
      if (L.tab === "model") {
        L.learning = await call("/api/lab/learning?lang=" + S.lang) || L.learning;
        try { L.engine = L.home && L.home.awake ? await api("/api/engine-learning") : null; } catch (_) { L.engine = null; }
        try { L.models = (await api("/api/models")).models; } catch (_) { /* keep what is shown */ }
      }
      draw();
      clearTimeout(L.timer);
      const nightRunning = L.tab === "model" && L.engine && (L.engine.running || (L.models || []).some((m) => m.training_progress && m.training_progress.state === "downloading"));
      if (L.home && (L.home.experiments.some((e) => e.running) || nightRunning) && S.view === "lab") L.timer = setTimeout(load, 2500);
    }
    const act = async (path, body, after) => { L.busy = true; draw(); const out = await call(path, body); L.busy = false; if (out && after) after(out); await load(); return out; };
    const statusTag = (s) => tag(t("lab.status." + s), s === "done" ? "good" : s === "failed" ? "bad" : s === "running" ? "" : "neutral");

    function home() {
      const H = L.home;
      const done = H.experiments.filter((e) => e.status === "done").length;
      return [
        h("p", { class: "lead" }, t("lab.lead")),
        h("div", { class: "alerts" }, H.alerts.map((a) => h("div", { class: "alert" }, t("lab.alerts." + a)))),
        h("div", { class: "stats" },
          [[H.awake || t("lab.none"), t("lab.stat_life")], [num(H.experiments.length, 0), t("lab.stat_campaigns")], [num(done, 0), t("lab.stat_done")],
           [num(H.observers.length, 0), t("lab.stat_observers")], [num(H.usage.requests, 0) + " / " + num(H.usage.limit.max_requests, 0), t("lab.stat_requests")]]
            .map(([value, label]) => h("div", { class: "card stat" }, h("b", {}, value), h("span", {}, label)))),
        h("div", { class: "section-title", style: "margin-top:22px" }, t("lab.tabs.hypotheses")),
        table([t("lab.col_h"), t("lab.col_title"), t("lab.col_impl"), t("lab.col_research")],
          H.hypotheses.map((x) => [x.id, x.title, tag(x.implementation_label, x.implementation === "implemented" ? "good" : x.implementation === "partial" ? "" : "bad"),
            tag(x.research_label, x.research === "not_measured" ? "neutral" : "")])),
        h("p", { class: "hint", style: "margin-top:10px" }, t("lab.status_hint"))];
    }

    function hypotheses() {
      const H = L.home, V = L.verdict || (L.verdict = {});
      return H.hypotheses.map((x) => h("section", { class: "card hyp" },
        h("div", { class: "hyp-head" }, h("b", {}, x.id + " · " + x.title),
          tag(x.implementation_label, x.implementation === "implemented" ? "good" : x.implementation === "partial" ? "" : "bad"),
          tag(x.research_label, x.research === "not_measured" ? "neutral" : "")),
        h("p", {}, x.claim),
        h("div", { class: "kv" }, h("b", {}, t("lab.control")), h("span", {}, x.control), h("b", {}, t("lab.limits")), h("span", {}, x.limits),
          h("b", {}, t("lab.protocols")), h("span", {}, x.protocols.join(", ") || t("lab.none")),
          h("b", {}, t("lab.campaigns")), h("span", {}, x.campaigns.length ? num(x.campaigns.length, 0) : t("lab.not_measured"))),
        x.metrics.length ? table([t("lab.col_metric"), t("lab.col_unit"), t("lab.col_level"), t("lab.col_state")],
          x.metrics.map((m) => [m.metric_id, m.unit, m.level_label, m.not_computable ? tag(t("lab.na") + " : " + m.not_computable, "bad") : tag(t("lab.computable"), "good")])) : null,
        x.verdict ? h("p", { class: "small", style: "margin-top:8px" }, t("lab.verdict_by", { who: x.verdict.by, when: when(x.verdict.utc) })) : null,
        x.campaigns.length ? h("div", { class: "verdict" },
          select(V[x.id] || "", [["", t("lab.verdict_none")], ["provisionally_supported", t("lab.verdicts.provisionally_supported")],
            ["not_supported", t("lab.verdicts.not_supported")], ["refuted_on_protocol", t("lab.verdicts.refuted_on_protocol")]], (v) => { V[x.id] = v; }),
          h("input", { placeholder: t("lab.your_name"), "aria-label": t("lab.your_name"), value: L.who || "", oninput: (e) => { L.who = e.target.value; } }),
          h("button", { class: "btn", onclick: () => act("/api/lab/verdict", { hypothesis: x.id, verdict: V[x.id] || null, who: L.who || "", experiment_id: x.campaigns[0] }) }, t("lab.verdict_save")),
          h("span", { class: "hint" }, t("lab.verdict_hint"))) : null));
    }

    function results() {
      const E = L.expData;
      if (!E) return null;
      const e = E.experiment, R = E.results, doneRuns = e.runs.filter((r) => r.status === "done").length;
      const levels = tr("lab.levels");
      const out = [h("div", { class: "hyp-head" }, h("b", {}, e.protocol_id + " · " + when(e.created_utc)), statusTag(e.running ? "running" : e.status),
        h("span", { class: "small muted" }, t("lab.runs", { done: doneRuns, total: e.runs.length }))),
        h("div", { class: "kv" }, h("b", {}, t("lab.t0")), h("span", { class: "mono" }, e.baseline_snapshot_sha256.slice(0, 16)),
          h("b", {}, t("lab.protocol_hash")), h("span", { class: "mono" }, e.protocol_sha256.slice(0, 16)),
          h("b", {}, t("lab.results_hash")), h("span", { class: "mono" }, e.results_sha256 ? e.results_sha256.slice(0, 16) : t("lab.na"))),
        e.anomalies.length ? h("div", { class: "alert" }, t("lab.anomalies") + " : " + e.anomalies.join(" · ")) : null];
      if (R) {
        out.push(h("p", { class: "hint" }, t("lab.unit_hint", { n: R.units.length, planned: R.units_planned })),
          h("div", { class: "section-title", style: "margin-top:14px" }, t("lab.primary")),
          table([t("lab.col_condition"), t("lab.col_distance"), t("lab.col_excess"), t("lab.col_interval"), t("lab.col_test"), t("lab.col_evidence")],
            R.divergence.map((d) => { const x = d.excess_over_twin; return [d.condition, num(d.mean_distance), x ? signed(x.mean_difference) : t("lab.no_twin"),
              x ? range(x.interval_95) : t("lab.na"), x ? num(x.p_sign_flip) : t("lab.na"), h("span", { class: "mono" }, d.evidence_id)]; })),
          h("div", { class: "section-title", style: "margin-top:18px" }, t("lab.comparisons")),
          h("p", { class: "hint", style: "margin-bottom:8px" }, t("lab.mechanism_hint")),
          table([t("lab.col_metric"), t("lab.col_condition"), t("lab.col_level"), t("lab.col_diff"), t("lab.col_effect"), t("lab.col_interval"), t("lab.col_test")],
            R.comparisons.filter((c) => !c.metric_id.startsWith("tech.")).map((c) => [c.metric_id, c.condition, levels[c.level], signed(c.mean_difference),
              num(c.effect_size_dz), range(c.interval_95), num(c.p_sign_flip)])),
          h("div", { class: "btn-row", style: "margin-top:14px" },
            h("button", { class: "btn primary", disabled: L.busy, onclick: () => act("/api/lab/report/build", { experiment_id: e.experiment_id, language: S.lang, author: L.who || "" }, () => { L.tab = "reports"; }) }, t("lab.build_report")),
            h("button", { class: "btn", disabled: L.busy, onclick: () => act("/api/lab/review", { experiment_id: e.experiment_id, blind: L.blind, order: L.home.observers.slice(0, 3).map((o) => o.observer_id) }) }, t("lab.review")),
            h("label", { class: "check" }, h("input", { type: "checkbox", checked: L.blind, onchange: (ev) => { L.blind = ev.target.checked; } }), t("lab.blind"))),
          h("p", { class: "hint" }, t("lab.review_hint")));
        for (const review of E.reviews || []) out.push(h("div", { class: "review" }, review.steps.map(entry)));
      }
      return h("section", { class: "card" }, out);
    }

    function entry(x) {
      const kind = x.kind === "question" ? "q" : x.kind === "error" ? "err" : "a";
      return h("div", { class: "entry " + kind },
        h("div", { class: "entry-head" }, x.name ? h("b", {}, x.name) : null, tag(t("lab.kinds." + x.kind)), x.llm ? tag(x.llm) : null,
          (x.invalid_citations || []).length ? tag(t("lab.invalid", { n: x.invalid_citations.length }), "bad") : null,
          (x.evidence || []).length && x.kind === "answer" ? tag(t("lab.cited", { n: x.evidence.length }), "good") : null),
        h("div", { class: "entry-text" }, x.kind === "error" ? code(x.text) : x.text),
        (x.invalid_citations || []).length ? h("div", { class: "hint" }, t("lab.invalid_hint") + " " + x.invalid_citations.join(", ")) : null);
    }

    function experiments() {
      const H = L.home;
      const start = async (p, fromLife) => {
        if (!L.approve) { L.error = t("lab.approve_first"); return draw(); }
        const made = await act("/api/lab/experiment/create", { protocol_id: p.protocol_id, version: p.protocol_version, approved: true, from_life: fromLife });
        if (made) { L.exp = made.experiment_id; await act("/api/lab/experiment/start", { id: made.experiment_id }); }
      };
      return [
        h("p", { class: "hint" }, t("lab.exp_lead")),
        h("label", { class: "check approve" }, h("input", { type: "checkbox", checked: !!L.approve, onchange: (e) => { L.approve = e.target.checked; } }), t("lab.approve")),
        h("div", { class: "section-title", style: "margin-top:14px" }, t("lab.protocols")),
        H.protocols.map((p) => h("section", { class: "card proto" },
          h("div", { class: "hyp-head" }, h("b", {}, p.protocol_id + " · " + p.title_label), h("span", { class: "small muted" }, "v" + p.protocol_version),
            tag(t("lab.pstatus." + p.status), p.status === "executable" ? "good" : "neutral"), p.locked ? tag(t("lab.locked")) : null,
            p.hypotheses.map((x) => tag(x, "neutral"))),
          p.status === "executable"
            ? [h("p", { class: "small muted" }, t("lab.proto_detail", { conditions: p.conditions.map((c) => c.name).join(", "), seeds: p.seeds.length, primary: p.primary_outcome })),
               h("div", { class: "btn-row" },
                 h("button", { class: "btn primary", disabled: L.busy, onclick: () => start(p, false) }, t("lab.run_synthetic")),
                 H.awake ? h("button", { class: "btn", disabled: L.busy, onclick: () => start(p, true) }, t("lab.run_copy", { name: H.awake })) : null,
                 h("button", { class: "btn", disabled: L.busy, onclick: () => { const v = p.protocol_version.split(".").map(Number); v[1] += 1;
                   act("/api/lab/protocol/duplicate", { id: p.protocol_id, version: p.protocol_version, new_version: v.join(".") }); } }, t("lab.duplicate")))]
            : h("p", { class: "small muted" }, t("lab.spec_only") + (p.reason ? " " + p.reason + "." : "")))),
        h("div", { class: "section-title", style: "margin-top:22px" }, t("lab.campaigns")),
        H.experiments.length ? table([t("lab.col_protocol"), t("lab.col_date"), t("lab.col_state"), t("lab.col_runs"), ""],
          H.experiments.map((e) => [e.protocol_id, when(e.created_utc), statusTag(e.running ? "running" : e.status),
            e.runs.filter((r) => r.status === "done").length + " / " + e.runs.length,
            h("div", { class: "btn-row" },
              h("button", { class: "btn small-btn", onclick: () => { L.exp = e.experiment_id; L.expData = null; load(); } }, t("lab.open")),
              e.running ? h("button", { class: "btn small-btn", onclick: () => act("/api/lab/experiment/cancel", { id: e.experiment_id }) }, t("lab.cancel"))
                : e.status !== "done" ? h("button", { class: "btn small-btn", onclick: () => act("/api/lab/experiment/start", { id: e.experiment_id }) }, t("lab.resume")) : null,
              !e.running ? h("button", { class: "btn small-btn", onclick: () => { if (L.exp === e.experiment_id) { L.exp = null; L.expData = null; } act("/api/lab/experiment/delete", { id: e.experiment_id }); } }, t("lab.delete")) : null)]))
          : h("p", { class: "muted" }, t("lab.no_campaign")),
        results()];
    }

    function observers() {
      const H = L.home, D = L.obsData, O = H.options;
      const names = (group, list) => list.map((v) => [v, t("lab." + group + "." + v)]);
      const list = h("div", { class: "obs-list" },
        H.observers.map((o) => h("button", { class: "obs" + (L.obs === o.observer_id ? " on" : ""), onclick: () => { L.obs = o.observer_id; L.obsData = null; load(); } },
          h("b", {}, o.name), h("span", { class: "small muted" }, t("lab.roles." + o.role)),
          h("span", { class: "small muted" }, (o.engine.kind === "none" ? t("lab.engines.none") : o.engine.kind + (o.engine.model ? " · " + o.engine.model : "")) + " · " + t("lab.modes." + o.mode)))),
        h("button", { class: "btn", onclick: () => act("/api/lab/observer/create", { name: t("lab.new_observer", { n: H.observers.length + 1 }), role: "explorer", language: S.lang },
          (o) => { L.obs = o.observer_id; }) }, t("lab.add_observer")));
      if (!D) return [h("p", { class: "hint" }, t("lab.obs_lead")), list];
      const p = D.profile, change = (changes) => act("/api/lab/observer/update", { id: p.observer_id, changes });
      const text = (key, value) => h("input", { value: value || "", onchange: (e) => change({ [key]: e.target.value }) });
      const engine = (k, v) => change({ engine: { ...p.engine, [k]: v } });
      const campaigns = L.home.experiments.filter((e) => e.status === "done");
      if (!L.askExp && campaigns.length) L.askExp = campaigns[0].experiment_id;
      const form = h("section", { class: "card" }, h("div", { class: "section-title" }, t("lab.profile")),
        h("div", { class: "grid-form" },
          field(t("lab.f_name"), text("name", p.name)), field(t("lab.f_role"), select(p.role, names("roles", O.roles), (v) => change({ role: v }))),
          field(t("lab.f_mode"), select(p.mode, names("modes", O.modes), (v) => change({ mode: v })), t("lab.mode_hint")),
          field(t("lab.f_language"), select(p.language, [["fr", "Français"], ["en", "English"]], (v) => change({ language: v })), t("lab.language_hint")),
          field(t("lab.f_engine"), select(p.engine.kind, names("engines", O.engines), (v) => change({ engine: { kind: v } }))),
          p.engine.kind !== "none" ? field(t("lab.f_model"), h("input", { value: p.engine.model || "", spellcheck: "false", onchange: (e) => engine("model", e.target.value) })) : null,
          ["local", "compatible"].includes(p.engine.kind) ? field(t("lab.f_url"), h("input", { value: p.engine.base_url || "", spellcheck: "false", onchange: (e) => engine("base_url", e.target.value) })) : null,
          !["none", "local"].includes(p.engine.kind) ? field(t("lab.f_key"), h("input", { type: "password", autocomplete: "off", placeholder: p.has_key ? "••••••••" : "",
            onchange: (e) => act("/api/lab/observer/key", { id: p.observer_id, key: e.target.value }) }), p.has_key ? t("lab.key_set") : t("lab.key_hint")) : null,
          field(t("lab.f_access"), select(p.access, names("access", O.access), (v) => change({ access: v })), t("lab.access_hint")),
          field(t("lab.f_requests"), h("input", { type: "number", min: 0, value: p.budget.max_requests, onchange: (e) => change({ budget: { ...p.budget, max_requests: Number(e.target.value) } }) }),
            t("lab.used", { n: num(p.usage.requests, 0), chars: num(p.usage.chars, 0) })),
          field(t("lab.f_chars"), h("input", { type: "number", min: 0, value: p.budget.max_chars, onchange: (e) => change({ budget: { ...p.budget, max_chars: Number(e.target.value) } }) })),
          p.engine.kind !== "none" && p.engine.kind !== "anthropic" ? field(t("lab.f_temperature"), h("input", { type: "number", min: 0, max: 2, step: 0.1, value: p.temperature == null ? "" : p.temperature,
            onchange: (e) => change({ temperature: e.target.value === "" ? null : Number(e.target.value) }) })) : null),
        field(t("lab.f_hypotheses"), h("div", { class: "checks" }, L.home.hypotheses.map((x) => h("label", { class: "check" },
          h("input", { type: "checkbox", checked: p.hypotheses.includes(x.id), onchange: (e) => change({ hypotheses: e.target.checked ? p.hypotheses.concat(x.id) : p.hypotheses.filter((i) => i !== x.id) }) }), x.id)))),
        field(t("lab.f_instructions"), h("textarea", { rows: 3, onchange: (e) => change({ instructions: e.target.value }) }, p.instructions)),
        h("div", { class: "btn-row" },
          h("button", { class: "btn", disabled: L.busy, onclick: async () => { const r = await act("/api/lab/observer/test", { id: p.observer_id });
            if (r) { L.test = r.offline ? t("lab.test_offline") : r.ok ? t("lab.test_ok") : t("lab.test_failed", { error: code(r.error) }); draw(); } } }, t("lab.test")),
          h("button", { class: "btn", disabled: L.busy, onclick: () => { L.obs = null; L.obsData = null; act("/api/lab/observer/delete", { id: p.observer_id }); } }, t("lab.delete_observer")),
          L.test ? h("span", { class: "small muted", role: "status" }, L.test) : null),
        h("p", { class: "hint", style: "margin-top:10px" }, t("lab.privacy_hint")));
      const question = h("textarea", { rows: 2, placeholder: t("lab.ask_placeholder"), "aria-label": t("lab.ask_placeholder") });
      const note = h("textarea", { rows: 2, placeholder: t("lab.note_placeholder"), "aria-label": t("lab.note_placeholder") });
      const chat = h("section", { class: "card" }, h("div", { class: "section-title" }, t("lab.chat", { name: p.name })),
        campaigns.length ? field(t("lab.f_campaign"), select(L.askExp, campaigns.map((e) => [e.experiment_id, e.protocol_id + " · " + when(e.created_utc)]), (v) => { L.askExp = v; }))
          : h("p", { class: "muted" }, t("lab.ask_no_campaign")),
        D.chat.length ? h("div", { class: "entries" }, D.chat.map(entry)) : h("p", { class: "muted" }, t("lab.chat_empty")),
        question,
        h("div", { class: "btn-row", style: "margin-top:8px" },
          h("button", { class: "btn primary", disabled: L.busy || !campaigns.length, onclick: () => { if (question.value.trim()) act("/api/lab/observer/ask", { id: p.observer_id, question: question.value, experiment_id: L.askExp, blind: L.blind }); } }, t("lab.ask")),
          h("label", { class: "check" }, h("input", { type: "checkbox", checked: L.blind, onchange: (e) => { L.blind = e.target.checked; } }), t("lab.blind"))),
        h("div", { class: "section-title", style: "margin-top:18px" }, t("lab.notes")),
        D.notes.length ? h("div", { class: "entries" }, D.notes.map((n) => entry({ ...n, kind: "note" }))) : h("p", { class: "muted" }, t("lab.notes_empty")),
        note,
        h("button", { class: "btn", style: "margin-top:8px", onclick: () => { if (note.value.trim()) act("/api/lab/observer/note", { id: p.observer_id, text: note.value, kind: "note", experiment_id: L.askExp }); } }, t("lab.note_save")));
      return [h("p", { class: "hint" }, t("lab.obs_lead")), list, h("div", { class: "grid-2 obs-detail" }, form, chat)];
    }

    function reportsTab() {
      const R = L.reports;
      if (!R) return [h("p", { class: "hint" }, "…")];
      return [h("p", { class: "hint" }, t("lab.reports_lead")),
        h("div", { class: "btn-row", style: "margin:10px 0" },
          h("input", { class: "who", placeholder: t("lab.your_name"), "aria-label": t("lab.your_name"), value: L.who || "", oninput: (e) => { L.who = e.target.value; } }),
          h("button", { class: "btn", onclick: () => call("/api/lab/report/reveal", {}) }, t("lab.reveal_reports"))),
        R.length ? R.map((r) => h("section", { class: "card" },
          h("div", { class: "hyp-head" }, h("b", {}, when(r.created_utc)), tag(r.language === "fr" ? "Français" : "English", "neutral"),
            tag(t("lab.rstatus." + r.status), r.status === "validated" ? "good" : "neutral"), r.llm_involved ? tag(t("lab.llm_involved")) : null),
          h("div", { class: "kv" }, h("b", {}, "Markdown"), h("span", { class: "mono" }, r.files.markdown), h("b", {}, "PDF"), h("span", { class: "mono" }, r.files.pdf),
            h("b", {}, t("lab.pack")), h("span", { class: "mono" }, r.files.pack)),
          r.status === "validated" ? h("p", { class: "small" }, t("lab.validated_by", { who: r.validated_by, when: when(r.validated_utc) }))
            : h("button", { class: "btn", style: "margin-top:10px", onclick: () => { if (!(L.who || "").trim()) { L.error = t("lab.name_first"); return draw(); } act("/api/lab/report/validate", { report_id: r.report_id, who: L.who }); } }, t("lab.validate"))))
          : h("p", { class: "muted" }, t("lab.no_report"))];
    }

    // The engine this life converses with: what it holds now, the nights that adapted it, and the controls.
    function engineCard() {
      const E = L.engine, k = (name, vars) => t("lab.learn.eng." + name, vars);
      const card = (...body) => h("section", { class: "card" }, h("div", { class: "section-title" }, k("title")), ...body.filter(Boolean));
      if (!E) return card(h("p", { class: "muted" }, k("no_life")));
      if (!E.model) return card(h("p", { class: "muted" }, k("not_embedded")));
      if (!E.model_learns) return card(h("p", { class: "muted" }, k("cannot", { model: E.model_name })));
      const st = E.settings, m = (L.models || []).find((x) => x.id === E.model) || {};
      const gb = (b) => (b / 1e9).toLocaleString(S.lang, { maximumFractionDigits: 1 }) + " " + t("models.gb");
      const post = (action, body) => act("/api/engine-learning/" + action, body);
      const active = E.versions.find((v) => v.version === E.active);
      const draft = L.engDraft || (L.engDraft = { steps: st.steps, rank: st.rank, growth: st.growth, max_rank: st.max_rank, max_adapter_parameters: st.max_adapter_parameters, nightly: st.nightly });
      const numberField = (key, min, max) => h("input", { type: "number", min, max, value: draft[key], oninput: (e) => { draft[key] = Number(e.target.value); } });
      const tp = m.training_progress || {};
      const reasons = (list) => (list || []).map((r) => k("reasons." + r)).join(", ");
      const detail = (row) => row.kind === "night" ? [k("decisions." + row.decision), row.version || "",
        reasons(((row.candidates || {})[row.chosen || "candidate"] || { verdict: {} }).verdict.reasons)].filter(Boolean).join(" · ")
        : row.kind === "skipped" ? k("reasons." + row.reason) : row.kind === "restore" ? (row.after || k("base_alone"))
        : row.kind === "corpus" ? "+" + row.added_train + " / +" + row.added_held_out : row.kind === "failed" ? row.error : row.kind === "settings" ? Object.keys(row.changes || {}).join(", ") : "";
      return card(
        h("div", { class: "kv" }, h("b", {}, k("model")), h("span", {}, E.model_name), h("b", {}, k("base_params")), h("span", {}, num(m.parameters, 0)),
          h("b", {}, k("in_use")), h("span", {}, active ? k("adapter", { version: active.version, params: num(active.adapter_parameters, 0) }) : k("base_alone")),
          h("b", {}, k("loaded")), h("span", { class: "mono" }, E.loaded.adapter ? E.loaded.adapter + " · " + (E.loaded.sha256 || "").slice(0, 16) : k("base_alone"))),
        !E.base_installed ? h("div", { class: "alert", style: "margin-top:12px" }, k("base_missing", { size: gb(m.training_size || 0), ram: 12 }), " ",
          tp.state === "downloading" || tp.state === "verifying" ? [h("span", {}, k("downloading")), bar(tp.done / Math.max(1, tp.total))]
            : h("button", { class: "btn small", onclick: () => act("/api/models/download", { id: E.model, part: "training" }) }, k("download_base")),
          tp.state === "error" ? h("div", { class: "error" }, tp.error) : null) : null,
        h("label", { class: "check", style: "margin-top:12px" }, h("input", { type: "checkbox", checked: st.enabled,
          onchange: (e) => post("configure", { changes: { enabled: e.target.checked }, who: L.who || "" }) }), k("enable")),
        h("p", { class: "hint" }, k("enable_hint") + (st.approved_by ? " · " + st.approved_by + ", " + when(st.approved_utc) : "")),
        h("div", { class: "grid2" },
          field(k("steps"), numberField("steps", 1, 2000)), field(k("rank"), numberField("rank", 1, 64)),
          h("label", { class: "check" }, h("input", { type: "checkbox", checked: draft.nightly, onchange: (e) => { draft.nightly = e.target.checked; } }), k("nightly")),
          h("label", { class: "check" }, h("input", { type: "checkbox", checked: draft.growth, onchange: (e) => { draft.growth = e.target.checked; } }), k("growth")),
          field(k("max_rank"), numberField("max_rank", 1, 128)), field(k("budget"), numberField("max_adapter_parameters", 1, 1e9))),
        h("p", { class: "hint" }, k("growth_hint")),
        h("div", { class: "btn-row" },
          h("button", { class: "btn", disabled: L.busy, onclick: () => { const changes = { ...draft }; L.engDraft = null; post("configure", { changes, who: L.who || "" }); } }, k("save")),
          E.running ? h("button", { class: "btn", onclick: () => post("cancel", {}) }, k("cancel"))
            : h("button", { class: "btn primary", disabled: L.busy || !E.base_installed || !st.enabled, onclick: () => post("run", {}) }, k("run"))),
        E.running ? h("p", { class: "hint" }, k("running", { step: (E.progress && E.progress.step) || "…" })) : null,
        h("p", { class: "small muted", style: "margin-top:10px" }, k("corpus", { train: num(E.corpus_items, 0), held: num(E.held_out_items, 0), pending: num(E.pending_items, 0) })),
        h("p", { class: "small muted" }, k("rules", { gain: num(E.thresholds.min_gain, 3), forget: num(E.thresholds.max_forgetting, 3), life: num(E.thresholds.max_life_forgetting, 3) })),
        h("div", { class: "section-title", style: "margin-top:16px" }, k("checkpoints")),
        E.versions.length ? table([k("col_version"), k("col_date"), k("col_rank"), k("col_params"), k("col_gain"), k("col_forget"), k("col_runtime"), ""],
          E.versions.slice().reverse().map((v) => [v.version, when(v.created), num(v.rank, 0), num(v.adapter_parameters, 0), signed(v.verdict.gain), signed(v.verdict.forgetting_reference),
            v.runtime_check && v.runtime_check.ran ? signed(v.runtime_check.difference) : t("lab.na"),
            v.version === E.active ? tag(k("current"), "good") : h("button", { class: "btn small", onclick: () => post("restore", { version: v.version, who: L.who || "" }) }, k("use"))]))
          : h("p", { class: "muted" }, k("none")),
        E.active ? h("button", { class: "btn", style: "margin-top:8px", onclick: () => post("restore", { version: null, who: L.who || "" }) }, k("use_base")) : null,
        h("div", { class: "section-title", style: "margin-top:16px" }, k("ledger")),
        E.ledger.length ? table([k("col_date"), k("col_kind"), k("col_detail")], E.ledger.slice().reverse().slice(0, 20).map((row) => [when(row.time), k("kinds." + row.kind), detail(row)]))
          : h("p", { class: "muted" }, k("none")),
        h("p", { class: "hint", style: "margin-top:10px" }, k("caveat")));
    }

    function model() {
      const M = L.learning;
      if (!M) return [h("p", { class: "hint" }, "…")];
      const c = M.capabilities, yes = (b) => (b ? t("lab.yes") : t("lab.no")), k = (name, vars) => t("lab.learn." + name, vars);
      const mod = M.modules || {}, own = mod.own_model, small = mod.learner, meta = mod.metacognition, world = mod.sandbox;
      const action = async (name, prompt) => { const r = await call("/api/lab/learning/action", { action: name, prompt }); if (r && "text" in r) L.sample = r.text; load(); };
      const decision = (d) => tag(k("decisions." + d), d === "accepted" ? "good" : "bad");
      const ownCard = h("section", { class: "card" }, ...[h("div", { class: "section-title" }, k("own_title")),
        !own ? h("p", { class: "muted" }, k("own_off")) : !own.born ? h("p", { class: "muted" }, k("own_unborn")) : null,
        own && own.born ? h("div", { class: "kv" }, h("b", {}, k("parameters")), h("span", {}, num(own.parameters, 0)), h("b", {}, k("layers")), h("span", {}, num(own.layers, 0)),
          h("b", {}, k("width")), h("span", {}, num(own.width, 0)), h("b", {}, k("lived_text")), h("span", {}, k("bytes", { n: num(own.corpus_bytes, 0) })),
          h("b", {}, k("trainings")), h("span", {}, num(own.jobs_accepted, 0) + " / " + num(own.jobs_total, 0)), h("b", {}, k("growths")), h("span", {}, num(own.growths.filter((g) => g.decision === "accepted").length, 0)),
          h("b", {}, k("weights")), h("span", { class: "mono" }, (own.weights_sha256 || "").slice(0, 16))) : null,
        own && own.jobs.length ? h("div", {}, h("div", { class: "section-title", style: "margin-top:16px" }, k("jobs") + " · " + k("loss_unit")),
          table([k("col_job"), t("lab.col_decision"), k("col_before"), k("col_after"), k("col_params"), k("col_seconds")],
            own.jobs.map((j) => [num(j.job, 0), decision(j.decision), num(j.heldout_loss_before, 3), num(j.heldout_loss_candidate, 3), num(j.trainable_parameters, 0), num(j.seconds, 1)]))) : null,
        own && own.growths.length ? h("div", {}, h("div", { class: "section-title", style: "margin-top:16px" }, k("growth_log")),
          table([k("col_layers"), k("col_params"), k("col_same"), t("lab.col_decision")],
            own.growths.map((g) => [g.layers_before == null ? "" : g.layers_before + " → " + g.layers_after, num(g.parameters_before || g.parameters, 0) + (g.parameters_after ? " → " + num(g.parameters_after, 0) : ""),
              g.function_preserved == null ? "" : yes(g.function_preserved), decision(g.decision)]))) : null,
        own && own.born ? h("div", { class: "btn-row", style: "margin-top:12px" },
          h("button", { class: "btn", onclick: () => action("own_sample", "") }, k("sample")),
          h("button", { class: "btn", disabled: !own.can_roll_back, onclick: () => action("own_rollback") }, k("rollback"))) : null,
        own && L.sample ? h("pre", { class: "sample" }, L.sample) : null,
        h("p", { class: "hint", style: "margin-top:10px" }, k("own_caveat"))].filter(Boolean));
      const smallCard = h("section", { class: "card" }, ...[h("div", { class: "section-title" }, k("learner_title")),
        !small ? h("p", { class: "muted" }, k("learner_off")) : h("div", { class: "kv" }, h("b", {}, k("parameters")), h("span", {}, num(small.parameters, 0)),
          h("b", {}, k("experts")), h("span", {}, num(small.experts.length - 1, 0) + " / " + num(small.quota_experts - 1, 0)), h("b", {}, k("episodes")), h("span", {}, num(small.episodes, 0)),
          h("b", {}, k("trained")), h("span", {}, yes(small.trained)), h("b", {}, k("weights")), h("span", { class: "mono" }, small.weights_sha256.slice(0, 16))),
        small && small.manifests.length ? table([t("lab.col_decision"), k("col_before"), k("col_after"), k("col_params")],
          small.manifests.map((m) => [decision(m.decision), num(m.heldout_loss_before, 3), num(m.heldout_loss_after, 3), num(m.trainable_parameters, 0)])) : null,
        small ? h("button", { class: "btn", style: "margin-top:12px", onclick: () => action("learner_rollback") }, k("learner_reset")) : null].filter(Boolean));
      const others = h("section", { class: "card" }, h("div", { class: "section-title" }, k("other_title")),
        h("div", { class: "kv" }, h("b", {}, k("meta")), h("span", {}, meta ? k("meta_line", { n: num(meta.n, 0), brier: num(meta.brier, 3), alerts: num(meta.alerts, 0), revisions: num(meta.revisions, 0) }) : k("off")),
          h("b", {}, k("world")), h("span", {}, world ? k("world_line", { steps: num(world.steps, 0), contexts: num(world.contexts_learned, 0) }) : k("off"))));
      return [h("p", { class: "lead" }, k("lead")),
        h("div", { class: "alert" }, M.message), h("ul", { class: "reasons" }, M.reasons.map((r) => h("li", {}, r))),
        h("div", { class: "alert" }, M.growth),
        h("input", { class: "who", placeholder: t("lab.your_name"), "aria-label": t("lab.your_name"), value: L.who || "", oninput: (e) => { L.who = e.target.value; } }),
        engineCard(), ownCard, smallCard, others,
        h("section", { class: "card" }, h("div", { class: "section-title" }, t("lab.machine")),
          h("div", { class: "kv" }, h("b", {}, t("lab.m_inference")), h("span", {}, yes(c.inference)), h("b", {}, k("m_training")), h("span", {}, yes(c.training_available)),
            h("b", {}, k("m_module")), h("span", {}, yes(c.module_training_available)), h("b", {}, k("m_growth")), h("span", {}, yes(c.growth_available)),
            h("b", {}, k("m_engine")), h("span", {}, yes(c.engine_training_available)), h("b", {}, "PyTorch / PEFT"), h("span", {}, yes(c.torch) + " / " + yes(c.peft)),
            h("b", {}, "GPU"), h("span", {}, c.gpu || t("lab.none")), h("b", {}, t("lab.m_memory")), h("span", {}, c.free_memory_gb == null ? t("lab.na") : num(c.free_memory_gb, 1) + " " + t("models.gb")),
            h("b", {}, t("lab.m_disk")), h("span", {}, num(c.free_disk_gb, 1) + " " + t("models.gb")))),
        h("section", { class: "card" }, h("div", { class: "section-title" }, k("engine_title")), h("p", { class: "hint", style: "margin-bottom:10px" }, k("engine_note")),
          M.manifests.length ? table([t("lab.col_model"), t("lab.col_method"), t("lab.col_adapters"), t("lab.col_added"), t("lab.col_decision")],
            M.manifests.map((m) => [m.base_model_id, t("lab.methods." + m.training_method), num(m.trainable_adapter_parameters, 0), num(m.added_module_parameters, 0), t("lab.decisions." + m.decision)]))
            : h("p", { class: "muted" }, t("lab.no_model"))),
        h("button", { class: "btn", onclick: () => window.FW.go("settings") }, t("lab.choose_model"))];
    }

    function draw() {
      if (S.view !== "lab") return;
      const body = !L.home ? [h("p", { class: "hint" }, L.error || "…")]
        : L.tab === "home" ? home() : L.tab === "hypotheses" ? hypotheses() : L.tab === "experiments" ? experiments()
        : L.tab === "observers" ? observers() : L.tab === "reports" ? reportsTab() : model();
      box.replaceChildren(...[
        h("div", { class: "tabs lab-tabs", role: "tablist" }, TABS.map((id) => h("button", { class: L.tab === id ? "on" : "", role: "tab", "aria-selected": String(L.tab === id),
          onclick: () => { L.tab = id; L.error = ""; load(); } }, t("lab.tabs." + id)))),
        L.home && L.error ? h("div", { class: "error", role: "alert" }, L.error) : null,
        h("div", { class: "lab-body" }, body.flat().filter(Boolean))].filter(Boolean));
    }
    draw();
    load();
    return {};
  }

  window.FWLab = { view, settings, gauges };
})();
