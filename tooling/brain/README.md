# Local Three.js runtime

The Python application ships its browser runtime in `freewill/ui/`; users do not
need Node.js, npm, a CDN, or an internet connection to draw the brain.

To rebuild the checked-in runtime after a deliberate dependency update:

```sh
cd tooling/brain
npm ci
npm run build
```

`brain-shape.js` contains every second vertex of `brain_vertex_low.obj` from
RichardGeorgeDavis/Neural-Network-Prototype at commit
`f68713cdb32d49c953ff1ba6eb345813d7d2a5a0` (7,241 points). Coordinates are
illustrative anatomy. They never represent measured neurons or model weights.
The renderer places Freewill's real functional zones and memories separately.

See `freewill/ui/THIRD_PARTY_NOTICES.txt` for the upstream MIT notices.

## Tests

The graph's fidelity contracts need only Node.js; run from the repository root:

```sh
node --test tests/test_brain_contract.cjs
```

For the browser smoke test, run from this directory after `npm ci`:

```sh
npx playwright install chromium
npm run test:browser
```

The test starts its own Python service with a temporary, simulated life and real
memory links. It never opens existing user lives or calls a model provider.
It checks the GPU view, real events, memory links, idle expiry, controls, memory
navigation, sleep, reduced motion, light/dark themes and the Canvas fallback.
Screenshots are written to a temporary directory, or `FREEWILL_ARTIFACTS`.
Use `PYTHON` to select a Python interpreter, `CHROMIUM_EXECUTABLE_PATH` for an
existing Chromium installation, and `FREEWILL_PLAYWRIGHT` for an existing module.
`FREEWILL_NO_SANDBOX=1` is available for isolated CI containers lacking a browser
sandbox; ordinary local runs keep Chromium's sandbox enabled.
