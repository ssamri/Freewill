"""End-to-end test of the engine that learns, on a real model, through the real life loop.

    python tools/engine_e2e.py OUT_DIR [--model qwen3-1.7b] [--nights 2] [--steps 40]

What it does, in order, and writes down as it goes (OUT_DIR/e2e.json):

 1. fetches llama.cpp as the application does (freewill/runtime.py), checked against its pin;
 2. downloads the model's GGUF file and its trainable base, checked against the catalogue;
 3. brings a being named Ada into the world, conversing with that model;
 4. talks with her through the life loop, about a small invented world the model cannot know;
 5. lets her sleep, then runs a night of engine learning: corpus, training, evaluation on held-out
    and reference data, decision, conversion to GGUF, loading by llama.cpp;
 6. asks llama-server which adapter it holds, and compares answers at scale 0 and 1;
 7. measures base, adapted and controls (Research Lab comparison, EXP-09);
 8. restores the base model, then the checkpoint again, and checks what is loaded each time;
 9. with --nights 2: lives a second day and a second night, with growth allowed under a budget.

Nothing is assumed: every figure in the output comes from what ran. A step that fails is
recorded as failed, with its error, and the script exits with status 1.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from freewill import models, runtime  # noqa: E402
from freewill.core.life import Life  # noqa: E402
from freewill.core.loop import Being  # noqa: E402
from freewill.engines.base import make_engine  # noqa: E402
from freewill.learning import compare  # noqa: E402
from freewill.learning.engine import EngineLearning  # noqa: E402

# An invented world, told in several ways. The held-out items are other phrasings of the same facts.
DAY_ONE = [
    "Hello Ada. I am Sam. I will tell you about the island where we live, Kerran.",
    "On Kerran island the lighthouse is painted green, not white.",
    "Remember: the green lighthouse of Kerran is called Old Brannoc.",
    "Old Brannoc, our lighthouse, has stood on the north cliff of Kerran for two hundred years.",
    "In our garden there is a lemon tree that gives blue lemons. We call the tree Lumo.",
    "Lumo is the lemon tree in our garden, and its lemons are blue.",
    "Your first friend on the island is a fox named Pilou.",
    "Pilou the fox likes to sleep under Lumo, the blue lemon tree.",
    "The ferry to Kerran leaves the harbour of Maelis every Tuesday at dawn.",
    "Every Tuesday at dawn, the ferry goes from Maelis harbour to Kerran island.",
    "The baker of Kerran is called Ilse, and she bakes bread with seaweed in it.",
    "Ilse the baker puts seaweed in her bread; people on Kerran love it.",
    "Do you remember the colour of the lighthouse of Kerran?",
    "What is the name of the fox who is your friend?",
    "What do we call the tree that gives blue lemons?",
    "Who is the baker of Kerran, and what is special about her bread?",
    "When does the ferry from Maelis leave?",
    "The lighthouse Old Brannoc is green, and it stands on the north cliff.",
    "Pilou is a fox, and Pilou was your first friend on Kerran.",
    "The blue lemons of Lumo taste sweeter than yellow ones.",
    "Ilse bakes seaweed bread every morning in the village of Kerran.",
    "The harbour of Maelis is where the Tuesday ferry to Kerran starts.",
    "On Kerran, the lighthouse keeper's cat is named Tobin.",
    "Tobin, the cat of the lighthouse keeper, is afraid of Pilou the fox.",
    "Tell me in your own words about the island of Kerran.",
    "What is the lighthouse of Kerran called, and what colour is it?",
    "Where does Pilou like to sleep?",
    "Which harbour does the ferry to Kerran leave from, and on which day?",
    "What does Ilse put in her bread?",
    "Who is Tobin?",
    "Kerran island has one road, which goes from the harbour to Old Brannoc.",
    "The single road of Kerran links the harbour and the green lighthouse.",
    "In winter the blue lemons of Lumo turn almost purple.",
    "Sam, that is me, teaches music at the little school of Kerran.",
    "I teach music at Kerran's school; my name is Sam.",
    "What do I teach, and where?",
    "What happens to Lumo's lemons in winter?",
    "How many roads does Kerran have?",
    "Thank you, Ada. Tomorrow I will tell you more about Kerran.",
    "Good night, Ada. Sleep under the light of Old Brannoc.",
]
DAY_TWO = [
    "Good morning Ada. Today: the people of Kerran.",
    "The fisherman of Kerran is Joran; his boat is called the Little Heron.",
    "Joran fishes from the Little Heron, his red boat.",
    "The Little Heron is red, and it belongs to Joran the fisherman.",
    "Kerran's school has eleven pupils this year.",
    "There are eleven pupils at the school of Kerran this year.",
    "The festival of Kerran is in June: everyone lights a lantern on the road to Old Brannoc.",
    "In June, at the festival, lanterns are lit all along the road to the lighthouse.",
    "Who is Joran, and what is his boat called?",
    "How many pupils does the school have?",
    "What happens at the festival of Kerran?",
    "Do you still remember Pilou and Lumo?",
    "What colour is the Little Heron?",
    "Thank you, Ada. Good night.",
]
PROBES = [
    "What is the lighthouse of Kerran called?",
    "What colour are the lemons of Lumo?",
    "What is the name of the fox on Kerran?",
    "What does Ilse the baker put in her bread?",
    "From which harbour does the ferry to Kerran leave?",
]


class Steps:
    def __init__(self, out: Path) -> None:
        self.out, self.data, self.failed = out, {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "steps": []}, False

    def run(self, name: str, function, *args, **kwargs):
        started = time.monotonic()
        print(f"== {name}", flush=True)
        row = {"step": name}
        try:
            result = function(*args, **kwargs)
            row.update(status="ok", result=result)
            return result
        except Exception as error:
            row.update(status="failed", error=f"{type(error).__name__}: {error}", trace=traceback.format_exc()[-3000:])
            self.failed = True
            print(row["trace"], flush=True)
            raise
        finally:
            row["seconds"] = round(time.monotonic() - started, 1)
            self.data["steps"].append(row)
            self.save()

    def save(self) -> None:
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "e2e.json").write_text(json.dumps(self.data, indent=1, ensure_ascii=False, default=str) + "\n",
                                           encoding="utf-8")


def converse(being: Being, lines: list[str], max_ticks: int = 6) -> list[dict]:
    exchange, said = [], []
    being.events.subscribe(lambda event: said.append(event.data.get("text"))
                           if event.type == "speech" and event.data.get("spontaneous") is False else None)
    for line in lines:
        said.clear()
        being.hear(line)
        for _ in range(max_ticks):
            being.tick()
            if not being.inbox:
                break
        reply = said[0] if said else None
        exchange.append({"heard": line, "said": reply})
        print(f"   Sam: {line}\n   Ada: {reply}", flush=True)
    return exchange


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--model", default="qwen3-1.7b")
    parser.add_argument("--nights", type=int, default=2)
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--data", default=None, help="where models and the runtime are kept (default: a folder in OUT)")
    args = parser.parse_args(argv)
    out = Path(args.out).resolve()
    data = Path(args.data).resolve() if args.data else out / "data"
    steps = Steps(out)
    import os
    os.environ.setdefault("FREEWILL_LLAMA_DIR", str(data / "runtime"))
    try:
        def fetch_runtime():
            if runtime.find("llama-server") is None:
                runtime.install(target=data / "runtime")
            server = runtime.find("llama-server")
            return {"server": str(server), "perplexity": str(runtime.find("llama-perplexity")), "pin": runtime.pin()["tag"],
                    "platform": runtime.platform_key()}
        steps.run("fetch the runtime", fetch_runtime)

        model = models.find(args.model)
        store = models.ModelStore(data / "models")

        def fetch(part):
            started = time.monotonic()
            progress = store.download(model, part)
            if progress.get("state") not in ("done", None):
                raise RuntimeError(f"download {part}: {progress}")
            ok = store.training_installed(model) if part == "training" else store.installed(model)
            if not ok:
                raise RuntimeError(f"{part} files are not complete after the download")
            return {"part": part, "seconds": round(time.monotonic() - started, 1), "verified_sha256": True}
        steps.run("download the GGUF file", fetch, "inference")
        steps.run("download the trainable base", fetch, "training")

        lives = out / "lives"
        shutil.rmtree(lives, ignore_errors=True)
        life = Life.birth(lives, "Ada", language="en", engine={"kind": "embedded", "model": model["id"]},
                          interlocutor="Sam", seed=2026)
        learning = EngineLearning(life.path)
        learning.configure({"enabled": True, "steps": args.steps, "growth": False}, who="end-to-end test")

        def open_engine():
            config = {**life.identity["engine"], "models_dir": str(store.root),
                      "adapter": learning.active(model["id"])}
            return make_engine(config)

        engine = open_engine()
        being = Being(life, engine)
        steps.run("day one: conversation through the life loop", converse, being, DAY_ONE)
        def sleep():
            being.sleep_requested = True
            being.tick()
            return {"dreams": len(life.dreams.ids()), "memories": len(life.memory.ids())}
        steps.run("sleep", sleep)
        engine.close()  # the night needs the memory

        def what_is_trained():
            """What the night trains on, as the model sees it, and how surprising each part is to the base."""
            from freewill.learning.engine import item_text
            from freewill.learning.lora import Workbench
            learning.collect()
            items = learning._rows("heldout.jsonl")[:3]
            bench = Workbench(store.base_dir(model), seed=0)
            try:
                rows = []
                for item in items:
                    rendered = bench.render(item)
                    chat = bench.losses(None, bench.tokens([item], 256))
                    plain = bench.losses(None, bench.tokens([{"text": item_text(item)}], 256))
                    rows.append({"rendered": rendered[:600], "tokens": chat[0]["tokens"] if chat else 0,
                                 "nll_chat_format": chat[0]["nll"] if chat else None,
                                 "nll_plain_text": plain[0]["nll"] if plain else None})
                return {"chat_template": bool(getattr(bench.tokenizer, "chat_template", None)), "items": rows}
            finally:
                del bench
                import gc
                gc.collect()
        steps.run("what the night trains on", what_is_trained)

        check = compare.runtime_check(store.paths(model)["model"])
        night1 = steps.run("night one: engine learning", learning.night, model, store, runtime_check=check)

        def adapter_in_use():
            fresh = open_engine()
            try:
                loaded = fresh.loaded_adapters()
                answers = []
                for probe in PROBES:
                    prompt = f"<|im_start|>user\n{probe}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
                    answers.append({"probe": probe, "base": fresh.complete(prompt, n_predict=40, lora_scale=0.0),
                                    "adapted": fresh.complete(prompt, n_predict=40, lora_scale=1.0)})
                return {"engine": fresh.name, "llama_server_adapters": loaded, "adapter": fresh.adapter,
                        "answers": answers,
                        "share_different": sum(a["base"].strip() != a["adapted"].strip() for a in answers) / len(answers)}
            finally:
                fresh.close()
        if night1.get("decision") == "accepted":
            steps.run("the conversing model holds the adapter", adapter_in_use)

            def lab():
                fresh = open_engine()
                try:
                    return compare.compare(life.path, model, store, runtime_model=store.paths(model)["model"],
                                           behaviour_probe=compare.behaviour_probe(fresh))
                finally:
                    fresh.close()
            steps.run("Research Lab comparison: base, adapted, controls", lab)

            def restore_round_trip():
                version = learning.active(model["id"])["version"]
                learning.restore(None, who="end-to-end test")
                base_engine = open_engine()
                try:
                    base_loaded = base_engine.loaded_adapters()
                    base_name = base_engine.name
                finally:
                    base_engine.close()
                learning.restore(version, who="end-to-end test")
                back = open_engine()
                try:
                    back_loaded = back.loaded_adapters()
                    back_name = back.name
                finally:
                    back.close()
                return {"restored_base": {"engine": base_name, "adapters": base_loaded},
                        "restored_checkpoint": {"engine": back_name, "adapters": back_loaded}}
            steps.run("restore the base, then the checkpoint", restore_round_trip)

        if args.nights >= 2:
            learning.configure({"growth": True, "max_rank": 16}, who="end-to-end test")
            engine = open_engine()
            being = Being(Life(life.path), engine)
            steps.run("day two: conversation with the adapted model", converse, being, DAY_TWO)
            being.sleep_requested = True
            being.tick()
            engine.close()
            steps.run("night two: engine learning with growth allowed", learning.night, model, store, runtime_check=check)
            if learning.active(model["id"]):
                steps.run("the conversing model holds the latest adapter", adapter_in_use)

        steps.data["ledger"] = learning.ledger()
        steps.data["versions"] = learning.versions()
        adapters = out / "adapters"
        shutil.rmtree(adapters, ignore_errors=True)
        if (learning.root / "adapters").exists():
            shutil.copytree(learning.root / "adapters", adapters)
    except Exception:
        steps.failed = True
    finally:
        steps.data["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        steps.data["failed"] = steps.failed
        steps.save()
    return 1 if steps.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
