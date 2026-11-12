"""Write the notes of a GitHub release: python tools/release_notes.py VERSION COMMIT

The notes name the exact commit that was built, give the section of the changelog
for that version, and say plainly what the Windows installer can and cannot do,
so that nobody assumes an installer carries every function of the main branch.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

USES = """\
## What this installer does, and what needs more

| Use | In the Windows installer | What it needs beyond the installer |
|---|---|---|
| Converse with a life, with the simulated engine, a remote API (Claude, GPT, Grok…) or an embedded GGUF model run by llama.cpp | Yes | An API key for a remote engine; the model file for an embedded one (downloaded by the application) |
| Train a LoRA adapter for the embedded engine (Qwen3 1.7B) during a life's nights | No | A source install with `pip install ".[lora]"` (PyTorch, PEFT, Transformers, gguf) and the trainable base of the model |
| Run and train Freewill 1.8B-V, the project's own model | No | A source install with `pip install ".[own-model]"`; a graphics card is strongly advised. A life's nights can train its adapters, but no real run has kept a night yet |

Tested: the test suite on Linux (CI), the installer and its self-test on Windows (CI), the embedded engine and its LoRA training on CPU (CI). **Not tested:** any graphics card, macOS, runs of several weeks. The installer is not signed yet.

Nothing in this release claims that a system is conscious or feels anything.
"""


def section(version: str) -> str:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(version)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not match:
        raise SystemExit(f"CHANGELOG.md has no section for {version}")
    return match.group(1).strip()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    version, commit = argv
    print(f"Built from commit `{commit}` (version {version}). The application shows the same commit under "
          "Settings, About this build.\n")
    print(section(version) + "\n")
    print(USES)
    print(f"French: [Journal des modifications](https://github.com/ssamri/Freewill/blob/{commit}/CHANGELOG.fr.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
