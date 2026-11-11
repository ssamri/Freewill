"""Check the catalogue of embedded models against its source, Hugging Face.

    python tools/catalogue.py            verify sizes, hashes and licences; exit 1 on any difference
    python tools/catalogue.py --write    rewrite freewill/models.json with what the source says

Every file the application may download is pinned by size and SHA-256 here,
so that what a person receives is exactly what was reviewed.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

CATALOGUE = Path(__file__).resolve().parent.parent / "freewill" / "models.json"
API = "https://huggingface.co/api/models/"


def fetch(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "freewill-catalogue-check"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    write = "--write" in sys.argv
    models = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    problems = []
    for model in models:
        try:
            tree = {entry["path"]: entry for entry in fetch(f"{API}{model['repo']}/tree/main")}
            info = fetch(f"{API}{model['repo']}")
        except (urllib.error.URLError, ValueError) as error:
            problems.append(f"{model['id']}: cannot read {model['repo']}: {error}")
            continue
        licence = (info.get("cardData") or {}).get("license") or next(
            (tag.split(":", 1)[1] for tag in info.get("tags", []) if tag.startswith("license:")), "?")
        if info.get("gated"):
            problems.append(f"{model['id']}: {model['repo']} is gated ({info['gated']}): it cannot be downloaded without an account")
        print(f"{model['id']}: licence declared by the source: {licence}; catalogue says: {model['licence']}")
        for key, prefix in (("file", ""), ("mmproj", "mmproj_")):
            name = model.get(key)
            if not name:
                continue
            entry = tree.get(name)
            if entry is None or "lfs" not in entry:
                near = sorted(path for path in tree if path.lower().endswith(".gguf"))
                problems.append(f"{model['id']}: {name} not found in {model['repo']}; it has: {near}")
                continue
            size, digest = entry["lfs"]["size"], entry["lfs"]["oid"]
            if (model.get(f"{prefix}size"), model.get(f"{prefix}sha256")) != (size, digest):
                problems.append(f"{model['id']}: {name} is {size} bytes, sha256 {digest}")
                model[f"{prefix}size"], model[f"{prefix}sha256"] = size, digest
    if write:
        CATALOGUE.write_text(json.dumps(models, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for problem in problems:
        print("DIFFERENCE:", problem)
    if problems and not write:
        print("----- catalogue as the source describes it -----")
        print(json.dumps(models, indent=2, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
