"use strict";

// Data/observation contracts for the real Brain class, without a GPU or browser.
// Only graphics allocation is substituted. These checks do not validate WebGL
// output, layout, accessibility, or frame performance.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const context = vm.createContext({
  window: {},
  document: { hidden: false },
  performance: { now: () => 1000 },
});
const rendererPath = path.join(__dirname, "../freewill/ui/brain.js");
vm.runInContext(fs.readFileSync(rendererPath, "utf8"), context, {
  filename: rendererPath,
});
const Brain = context.window.Brain;

function memory(id, links = [], extra = {}) {
  return {
    id, title: id, compartment: "shared", strength: 0.35,
    state: "complete", links, ...extra,
  };
}

function observation() {
  const brain = Object.create(Brain.prototype);
  Object.assign(brain, {
    running: true,
    labels: {},
    nodes: new Map(),
    pending: [],
    time: 1,
    userControls: { paused: false },
    waves: [],
    signals: new Array(220).fill(null),
    nextSignal: 0,
    // A small static surface is sufficient for data contracts; shape sampling
    // remains production code and is not being asserted by these tests.
    tissue: {
      pts: [[-0.5, 0.2, 0.2], [0.5, 0.2, 0.2]],
      grid: new Map(),
      cell: 0.2,
    },
    rebuildNodes() {
      this.nodeList = [...this.nodes.values()];
      this.nodeList.forEach((node, index) => { node.index = index; });
      this.nodePoints = {
        geometry: { attributes: { aSize: { array: new Float32Array(this.nodes.size) } } },
      };
    },
  });
  const emitted = { routes: [], flares: [], waves: [] };
  for (const [method, field] of [["signal", "routes"], ["flare", "flares"], ["addWave", "waves"]]) {
    const original = brain[method];
    brain[method] = function (...args) {
      emitted[field].push(args);
      return original.apply(this, args);
    };
  }
  brain.buildFixed();
  return { brain, emitted };
}

function memoryIds(brain) {
  return [...brain.nodes.values()].filter(node => node.kind === "memory").map(node => node.id).sort();
}

function associations(brain) {
  return Array.from(brain.edges).filter(edge => edge.kind === "memory")
    .map(edge => [edge.from, edge.to].sort().join(" / ")).sort();
}

function activityCount(emitted) {
  return emitted.routes.length + emitted.flares.length + emitted.waves.length;
}

test("the memory graph follows stored memories, without inferring associations from compartments", () => {
  const { brain } = observation();
  brain.setMemories([]);
  assert.deepEqual(memoryIds(brain), []);
  assert.equal(brain.counts.links, 0);

  brain.setMemories([memory("moments/a"), memory("moments/b")]);
  assert.deepEqual(memoryIds(brain), ["moments/a", "moments/b"]);
  assert.deepEqual(associations(brain), []);
  assert.equal(brain.counts.memories, 2);

  brain.setMemories([memory("moments/b")]);
  assert.deepEqual(memoryIds(brain), ["moments/b"]);
});

test("stored reciprocal links appear once; missing and self references create no association", () => {
  const { brain } = observation();
  brain.setMemories([
    memory("moments/a", ["moments/b", "moments/b", "moments/a", "moments/missing"]),
    memory("moments/b", ["moments/a"]),
    memory("moments/unrelated"),
  ]);
  assert.deepEqual(associations(brain), ["moments/a / moments/b"]);
  assert.equal(brain.counts.links, 1);
});

test("loading or refreshing memories and needs never fabricates activity", () => {
  const { brain, emitted } = observation();
  brain.setMemories([memory("moments/a")]);
  brain.setNeeds({ curiosity: 1, wonder: 0.8, company: 0.9, fatigue: 0.5 });
  brain.setMemories([memory("moments/a", [], { strength: 0.7 }), memory("moments/b")]);
  brain.setNeeds({ curiosity: 0.2, fatigue: 0.1 });
  assert.equal(activityCount(emitted), 0);
  assert.equal(brain.waves.length, 0);
  assert.equal(brain.signals.filter(Boolean).length, 0);
});

test("a real recall updates that memory and does not claim its neighbours were recalled", () => {
  const { brain, emitted } = observation();
  brain.setMemories([memory("moments/a", ["moments/b"]), memory("moments/b")]);
  const previousSize = brain.nodes.get("moments/a").size;
  brain.recall("moments/a", "subject", { strength: 0.85, state: "condensed" });

  assert.equal(brain.nodes.get("moments/a").data.strength, 0.85);
  assert.equal(brain.nodes.get("moments/a").data.state, "condensed");
  assert.ok(brain.nodes.get("moments/a").size > previousSize);
  assert.equal(brain.nodes.get("moments/b").data.strength, 0.35);
  assert.ok(emitted.routes.length > 0);
  assert.ok(emitted.routes.every(([from, to]) => from === "moments/a" && to === "@self"));
  assert.ok(!emitted.flares.some(([id]) => id === "moments/b"));
});

test("remember waits through partial responses and activates once the real memory arrives", () => {
  const { brain, emitted } = observation();
  brain.remember("moments/new", { title: "A new memory" });
  brain.setMemories([]);
  brain.time = 3;
  brain.setMemories([memory("moments/older")]);
  assert.equal(activityCount(emitted), 0);
  assert.ok(!brain.nodes.has("moments/new"));

  brain.setMemories([memory("moments/older"), memory("moments/new")]);
  assert.equal(emitted.flares.filter(([id]) => id === "moments/new").length, 1);
  assert.ok(emitted.routes.some(([from, to]) => from === "@self" && to === "moments/new"));
  const afterArrival = activityCount(emitted);
  brain.setMemories([memory("moments/older"), memory("moments/new")]);
  assert.equal(activityCount(emitted), afterArrival);
});

test("repeated partial responses do not keep an old remember event alive indefinitely", () => {
  const { brain, emitted } = observation();
  brain.remember("moments/late", {});
  brain.time = 5;
  brain.setMemories([]);
  brain.time = 11;
  brain.setMemories([]);
  brain.time = 14;
  brain.setMemories([memory("moments/late")]);
  assert.ok(brain.nodes.has("moments/late"));
  assert.equal(activityCount(emitted), 0, "late data may populate the graph without replaying stale activity");
});

test("a dream coactivates its real memories without inventing links between unrelated participants", () => {
  const { brain, emitted } = observation();
  brain.setMemories([
    memory("moments/a", ["moments/b"]),
    memory("moments/b", ["moments/a"]),
    memory("moments/c"),
  ]);
  brain.dream(["moments/a", "moments/b", "moments/c"], {});

  const coactivated = new Set(emitted.routes.filter(([, to]) => to === "~dream").map(([from]) => from));
  assert.deepEqual([...coactivated].sort(), ["moments/a", "moments/b", "moments/c"]);
  const memoryRoutes = emitted.routes.filter(([from, to]) => from.startsWith("moments/") && to.startsWith("moments/"));
  assert.ok(memoryRoutes.length > 0);
  assert.ok(memoryRoutes.every(([from, to]) => [from, to].sort().join(" / ") === "moments/a / moments/b"));
  assert.deepEqual(associations(brain), ["moments/a / moments/b"]);
});

test("a partially loaded dream waits for its participants and does not replay the known ones twice", () => {
  const { brain, emitted } = observation();
  brain.setMemories([memory("moments/a")]);
  brain.dream(["moments/a", "moments/b"], {});
  brain.setMemories([memory("moments/a")]);
  assert.equal(activityCount(emitted), 0);

  brain.setMemories([memory("moments/a"), memory("moments/b")]);
  for (const id of ["moments/a", "moments/b"]) {
    assert.equal(emitted.flares.filter(([activated]) => activated === id).length, 1);
  }
  const afterArrival = activityCount(emitted);
  brain.setMemories([memory("moments/a"), memory("moments/b")]);
  assert.equal(activityCount(emitted), afterArrival);
  assert.deepEqual(associations(brain), []);
});
