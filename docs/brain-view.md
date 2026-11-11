# The Brain view

**English** · [Français](brain-view.fr.md)

The view shows Freewill's memory and attention in a Three.js volume. Its
anatomical outline comes from the Neural Network Prototype model, used under the
MIT licence. The network on screen does not represent the neurons of the
language model, and the zones are not measured biological lobes.

## What drives the light

| Freewill data | Effect in the view |
| --- | --- |
| `stage` | A flow from the selected source to the central stage; quieter competitors; salience taken into account |
| `recall` | The named memory lights up and joins the stage; its strength and state are updated |
| `remember` | A signal to the memory actually kept, even if it loads after the event |
| `decision` | A distinct central response for welcoming or dismissing |
| `speech` | An outgoing flow to the conversation zone |
| `read` | The reading zone is activated |
| `sleep`, `dream`, `rest` | Sleep mode, activation of the memories taking part in the dream, return to the current state |
| `snapshot.needs` | A continuous level for the state of the needs; no fabricated periodic event |
| `/api/memory` | Nodes, compartments, strengths and the links saved between memories |

The cyan fibres of the outline are illustrative. Memory links are built only
from the saved `links` identifiers, then deduplicated. The source-to-stage paths
express the application's functions. The view creates no memory, no lasting
association and no cognitive activity. History can be read in the panel; it is
never replayed as if it had just happened.

The central core ("Core · self") is drawn in volume: translucent blue, violet
and pink petals around a bright heart, after Freewill's icon. Its shape, its slow
turn and its breathing are decorative; its brightness follows the real level of
the self (decisions, sleep). It keeps a persistent label and can be selected.
Memories remain visible as ringed, contrasted points; several titles are shown
without hovering, with priority to recently recalled memories. Labels avoid
overlapping and titles come from the saved data. The background tissue stays
quieter than these elements, including during waves of activity.

## Exploring

- Drag and use the wheel to turn and zoom.
- Select a source to inspect its function and its real weight.
- Click a memory to open its account.
- Use Rotate, Motion, Freeze view and Reset to adjust the rendering.
- Keyboard: Tab for the controls, Space to freeze the view, Home or 0 to reset when the canvas has the focus.

Freezing the view does not stop the being's life. The status shown comes from
the server: thinking, sleeping, waiting, hourly limit, retry or engine pause.
The system preference for reduced motion is respected.

## Architecture and distribution

`brain.js` keeps an interface independent of the cognitive loop:
`setMemories`, `stage`, `recall`, `remember`, `decision`, `speech`, `read`,
`dream`, `setNeeds`, `setAsleep`, `setSnapshot`, `setControls` and `destroy`.

Rendering uses grouped geometries, activation shaders, a bounded number of
signals and a spatial grid to build the fibres. No CDN is used.
`three.bundle.js`, `brain-shape.js` and the notices are shipped by setuptools
and PyInstaller. Without WebGL, `brain-canvas.js` provides a fallback rendering.
The build guide is in `tooling/brain/README.md`.

Recall events carry the memory's strength, state and phase directly, which
avoids re-reading the whole memory at each recall. Loading requests are
serialised, and older responses do not replace more recent known strengths.

Memory files and their indexes are published by atomic replacement, so that the
interface never reads a partial file during a recall or a sleep.

## Verification

The Python suite checks, among other things, the current modes during sleep and
errors, and the strengths carried by conscious and night-time recalls. The
browser checks cover real messages from the simulated engine, saved links, the
end of signals when idle, the controls, clicking on memories, the themes and the
fallback without WebGL. The simulated engine tests Freewill's mechanics with no
key and no call to an outside provider.
