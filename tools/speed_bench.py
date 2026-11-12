"""Measure how fast the local engines think, before and after the speed settings, on real Freewill requests.

    python tools/speed_bench.py OUT_DIR --part embedded [--data DIR] [--rounds 2]
    python tools/speed_bench.py OUT_DIR --part own [--data DIR] [--tokens 96]

The requests are recorded first: a being is born, spoken to in English and in French, and left to
think, through the real life loop (with the simulated engine, so that the requests do not depend on
the engine being measured). Every request it made, instructions and situation as the loop wrote
them, is then replayed, the same for every configuration, greedy (temperature 0), so that the
answers can be compared token for token.

--part embedded: Qwen3 1.7B through llama.cpp, fetched as the application fetches it. Configurations:
the threads Freewill used before (every logical core but one) against the physical cores, and no
drafting against llama.cpp's two n-gram drafters. Each configuration starts its own server; the
first request warms it and is not counted. The configurations run in turn, `--rounds` times.

--part own: Freewill 1.8B-V (Qwen3 1.7B + SigLIP2 base, from the pinned bases) in PyTorch, in
bfloat16 and float32, with and without the instructions read once and kept (FreewillVLM.answer).

Everything is written to OUT_DIR/speed.json: per request, the seconds, the tokens, what llama.cpp
says it reused from its cache and accepted from the drafts, and whether the answer is the same as
the reference configuration's. Nothing is summarised that was not measured.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from freewill.core.life import Life  # noqa: E402
from freewill.core.loop import Being  # noqa: E402
from freewill.engines import speed  # noqa: E402
from freewill.engines.base import EngineError  # noqa: E402
from freewill.engines.simulated import SimulatedEngine  # noqa: E402

LINES = {
    "en": ["Hello! I am Sam. Who are you?", "What would you like to learn first?",
           "I read a story today about a lighthouse keeper who counted the ships every night. "
           "Do you remember what I told you my name was?",
           "Tell me, in your own words, what you think about while I am away."],
    "fr": ["Bonjour ! Je suis Sam. Qui es-tu ?", "Qu'aimerais-tu apprendre en premier ?",
           "J'ai lu aujourd'hui l'histoire d'un gardien de phare qui comptait les bateaux chaque nuit. "
           "Te souviens-tu de mon prénom ?",
           "Dis-moi, avec tes mots, à quoi tu penses quand je ne suis pas là."],
}


class Recorder(SimulatedEngine):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[dict] = []

    def decide(self, system, prompt, schema, hint, images=None):
        self.requests.append({"system": system, "prompt": prompt, "schema": schema})
        return super().decide(system, prompt, schema, hint, images)


def record(folder: Path) -> list[dict]:
    requests = []
    for language, lines in LINES.items():
        life = Life.birth(folder / language, "Ada" if language == "en" else "Adele", language=language,
                          engine={"kind": "simulated"}, seed=7)
        engine = Recorder()
        being = Being(life, engine)
        for line in lines:
            being.hear(line)
            for _ in range(4):
                being.tick()
                if not being.inbox:
                    break
        for _ in range(3):   # a few moments alone: the subconscious proposes, the conscious decides
            being.tick()
        requests += [{**r, "language": language} for r in engine.requests]
    return requests


def machine() -> dict:
    return {"system": platform.system(), "release": platform.release(), "processor": platform.processor() or platform.machine(),
            "logical_cores": speed.logical_cores(), "physical_cores": speed.physical_cores(),
            "python": platform.python_version()}


def summary(rows: list[dict], reference: dict[int, str] | None) -> dict:
    seconds = [r["seconds"] for r in rows if "seconds" in r]
    out = {"requests": len(rows), "failed": sum("error" in r for r in rows),
           "seconds_total": round(sum(seconds), 2), "seconds_median": round(statistics.median(seconds), 3) if seconds else None}
    timed = [r["timings"] for r in rows if r.get("timings")]
    if timed:
        predicted = sum(t.get("predicted_n", 0) for t in timed)
        predicted_ms = sum(t.get("predicted_ms", 0) for t in timed)
        prompt = sum(t.get("prompt_n", 0) for t in timed)
        prompt_ms = sum(t.get("prompt_ms", 0) for t in timed)
        out.update({"tokens_generated": predicted, "generation_tokens_per_second": round(predicted / predicted_ms * 1000, 2) if predicted_ms else None,
                    "prompt_tokens_read": prompt, "prompt_tokens_per_second": round(prompt / prompt_ms * 1000, 2) if prompt_ms else None,
                    "prompt_tokens_reused_from_cache": sum(t.get("cache_n", 0) for t in timed),
                    "drafted": sum(t.get("draft_n", 0) for t in timed), "drafted_accepted": sum(t.get("draft_n_accepted", 0) for t in timed)})
    if reference is not None:
        compared = [r for r in rows if "answer" in r and r["index"] in reference]
        out["same_answer_as_reference"] = f"{sum(r['answer'] == reference[r['index']] for r in compared)}/{len(compared)}"
    return out


# -- llama.cpp ---------------------------------------------------------------------------------

def embedded(out: Path, data: Path, requests: list[dict], rounds: int) -> dict:
    from freewill import models, runtime
    from freewill.engines.embedded import EmbeddedEngine

    server = runtime.find("llama-server")
    if server is None:
        server = runtime.install(target=data / "runtime") / runtime.exe("llama-server")
    store = models.ModelStore(data / "models")
    model = models.find("qwen3-1.7b")
    if not store.installed(model):
        store.download(model)
    paths = store.paths(model)

    class Greedy(EmbeddedEngine):
        def _extra_body(self):
            return {**super()._extra_body(), "temperature": 0, "seed": 1}

    configurations = [
        ("before: logical cores - 1, no draft", {"threads": speed.threads_before(), "draft": "off"}),
        ("physical cores, no draft", {"threads": speed.threads(), "draft": "off"}),
        ("physical cores, ngram-simple draft", {"threads": speed.threads(), "draft": "ngram"}),
        ("physical cores, ngram-mod draft", {"threads": speed.threads(), "draft": "ngram-mod"}),
    ]
    results: dict = {"model": model["id"], "file": paths["model"].name, "runtime": runtime.pin()["tag"], "server": str(server),
                     "configurations": {name: {"settings": settings, "rounds": []} for name, settings in configurations}}
    reference: dict[int, str] | None = None
    for round_number in range(rounds):
        for name, settings in configurations:
            engine = Greedy(model, paths["model"], None, runtime=server, **settings)
            rows = []
            try:
                warm = requests[0]
                engine._ask(warm["system"], warm["prompt"], warm["schema"], None)
                for index, request in enumerate(requests):
                    started = time.perf_counter()
                    try:
                        answer = engine._ask(request["system"], request["prompt"], request["schema"], None)
                        rows.append({"index": index, "language": request["language"], "seconds": round(time.perf_counter() - started, 3),
                                     "answer": json.dumps(answer, ensure_ascii=False, sort_keys=True),
                                     "timings": getattr(engine, "last_timings", None)})
                    except EngineError as error:
                        rows.append({"index": index, "error": str(error)[:300]})
            except Exception as error:  # the server would not start with these settings: say so
                rows.append({"index": -1, "error": f"{type(error).__name__}: {str(error)[:400]}"})
            finally:
                engine.close()
            if reference is None and name.startswith("before") and not any("error" in r for r in rows):
                reference = {r["index"]: r["answer"] for r in rows}
            entry = {"round": round_number + 1, "summary": summary(rows, reference), "rows": rows}
            results["configurations"][name]["rounds"].append(entry)
            print(f"round {round_number + 1}  {name}: {json.dumps(entry['summary'])}", flush=True)
            for row in rows:
                if "error" in row:
                    print(f"    request {row['index']}: {row['error']}", flush=True)
            (out / "speed.json").write_text(json.dumps({**results, "machine": machine()}, indent=1, ensure_ascii=False), encoding="utf-8")
    if all(r["summary"]["failed"] == r["summary"]["requests"] for c in results["configurations"].values() for r in c["rounds"]):
        raise RuntimeError("every request failed in every configuration: nothing was measured")
    return results


# -- Freewill 1.8B-V ---------------------------------------------------------------------------

def own(out: Path, data: Path, requests: list[dict], tokens: int, count: int) -> dict:
    import torch
    from freewill.vlm import store
    from freewill.vlm.model import build

    bases = data / "bases-root"
    if not store.bases_ready(bases):
        store.fetch_bases(bases, log=lambda *a: print(*a, flush=True))
    chosen = requests[:count]
    fields = lambda r: ", ".join(f'"{n}"' for n in r["schema"]["properties"])  # noqa: E731
    results: dict = {"model": "freewill-1.8b-v (bases, untrained bridge: text only)", "max_new_tokens": tokens,
                     "torch": torch.__version__, "torch_threads": torch.get_num_threads(), "configurations": {}}
    for dtype in ("bfloat16", "float32"):
        model = build(bases / "bases", dtype=dtype)
        reference = None
        for reuse in (False, True):
            name = f"{dtype}, " + ("instructions read once and kept" if reuse else "instructions read every time (before)")
            model._head = None
            rows = []
            for index, request in enumerate(chosen):
                parts = [f"{request['system']}\n\n", ("cut",),
                         f"{request['prompt']}\n\nAnswer with one JSON object with exactly these keys: {fields(request)}.\n"]
                started = time.perf_counter()
                model.answer(parts, max_new_tokens=1, reuse=reuse)
                first = time.perf_counter() - started
                started = time.perf_counter()
                answer = model.answer(parts, max_new_tokens=tokens, reuse=reuse)
                rows.append({"index": index, "language": request["language"], "seconds_first_token": round(first, 3),
                             "seconds": round(time.perf_counter() - started, 3), "answer": answer})
                print(f"{name} #{index}: first token {first:.2f}s, {tokens} tokens {rows[-1]['seconds']:.2f}s", flush=True)
            if reference is None:
                reference = {r["index"]: r["answer"] for r in rows}
            entry = summary(rows, reference)
            entry["seconds_first_token_median"] = round(statistics.median(r["seconds_first_token"] for r in rows), 3)
            results["configurations"][name] = {"summary": entry, "rows": rows}
            print(f"{name}: {json.dumps(entry)}", flush=True)
            (out / "speed.json").write_text(json.dumps({**results, "machine": machine()}, indent=1, ensure_ascii=False), encoding="utf-8")
        del model
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--part", choices=("embedded", "own"), required=True)
    parser.add_argument("--data", default=None)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--tokens", type=int, default=96)
    parser.add_argument("--count", type=int, default=6)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    data = (Path(args.data) if args.data else out / "data").resolve()
    requests = record(out / "lives")
    (out / "requests.json").write_text(json.dumps(requests, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(requests)} requests recorded from the life loop "
          f"(instructions {min(len(r['system']) for r in requests)}-{max(len(r['system']) for r in requests)} characters)", flush=True)
    print(json.dumps(machine()), flush=True)
    try:
        if args.part == "embedded":
            embedded(out, data, requests, args.rounds)
        else:
            own(out, data, requests, args.tokens, args.count)
    except Exception:
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
