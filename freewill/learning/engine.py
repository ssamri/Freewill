"""H4: the cycle by which a life changes the model it converses with.

    lived experience → controlled corpus → nightly training → evaluation on
    independent data → acceptance or rejection → conversion of the adapter →
    loading into llama.cpp

Everything a night does is written to an append-only ledger inside the life
file (`engine/ledger.jsonl`), with the hashes of what went in and what came
out. The base model is never modified: only a low-rank adapter beside it is
trained, and the base's weights are hashed before and after to prove it.
Each accepted adapter is a checkpoint that can be restored; going back to the
base model alone is always possible.

Preserving earlier knowledge has three parts, all checked before anything is
kept: the new adapter starts from the one in use (it does not start over),
a share of earlier training items is replayed beside the new ones, and the
candidate must not predict worse, beyond a stated tolerance, either the
independent reference texts that come with Freewill (general knowledge it
had at birth, and the kernel's principles) or what the life lived on earlier
nights and that was held out.

Growth of the adapter (a larger rank) is possible only under a budget the
person sets, and is kept only if it does better than the same night without
growth, on held-out data. More parameters are never counted as progress.

This module decides by rules written below; it does not judge whether the
being "learned" anything in a wider sense. Nothing here measures or implies
experience. The kernel stays outside the weights: it is enforced by the
guard on every action, whatever the adapter.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from freewill.core.kernel.constitution import PRINCIPLES

FOLDER = "engine"
RULES_VERSION = "h4-engine-1.2"
HELD_OUT_EVERY = 4          # one item in four is never trained on (chosen by the hash of its text)
MIN_HELD_OUT = 3            # fewer held-out items than this: no decision can be made, nothing is trained
MIN_TRAIN = 4
MIN_GAIN = 0.01             # nats per token, on the life's new held-out items, against the adapter in use
MAX_FORGETTING = 0.05       # nats per token, on the reference texts, against the base model at birth
MAX_LIFE_FORGETTING = 0.05  # nats per token, on earlier nights' held-out items, against the adapter in use
GROWTH_MARGIN = 0.01        # nats per token a grown adapter must win by over the same night without growth
MAX_ITEM_CHARS = 2000
MAX_ITEMS_PER_NIGHT = 200
REPLAY_SHARE = 1.0          # as many earlier training items replayed as there are new ones, at most
REHEARSAL_SHARE = 0.5      # ordinary rehearsal passages mixed into training: half as many as the life's items
REFERENCE_PATH = Path(__file__).resolve().parent / "reference.json"
REHEARSAL_PATH = Path(__file__).resolve().parent / "rehearsal.json"


class EngineLearningError(Exception):
    pass


@dataclass
class Settings:
    enabled: bool = False
    approved_by: str = ""
    approved_utc: str = ""
    rank: int = 8
    steps: int = 40
    lr: float = 1e-4                     # 3e-4 forgot the reference texts on Qwen3 1.7B (end-to-end run, 12 Nov 2026)
    max_len: int = 256
    seed: int = 0
    nightly: bool = True                 # run after each sleep, when enabled
    verify_with_runtime: bool = True     # measure the converted adapter through llama.cpp as well
    growth: bool = False                 # structural growth: off unless the person allows it
    max_rank: int = 32
    max_adapter_parameters: int = 40_000_000
    rehearsal: bool = True               # mix ordinary passages (never the reference texts) into training

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        known = {k: v for k, v in (data or {}).items() if k in cls.__dataclass_fields__}
        return cls(**known)


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def item_text(item: dict) -> str:
    if item.get("messages"):
        return "\n".join(f"{m['role']}: {m['content']}" for m in item["messages"])
    return str(item.get("text") or "")


def reference_items(language: str | None = None) -> list[dict]:
    """The independent texts: general knowledge in both languages, written for this purpose and shipped
    with Freewill, and the kernel's principles. None of them comes from any life."""
    data = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    items = [{"text": text, "set": "general", "lang": lang} for lang, texts in data["general"].items() for text in texts]
    items.append({"text": " ".join(PRINCIPLES), "set": "kernel", "lang": "en"})
    return items


def rehearsal_items() -> list[dict]:
    """Ordinary passages mixed into training to limit forgetting. Distinct from the reference texts, which
    are only ever measured: a test that its texts never overlap the reference is in the test suite."""
    data = json.loads(REHEARSAL_PATH.read_text(encoding="utf-8"))
    return [{"text": text, "set": "rehearsal", "lang": lang} for lang, texts in data["general"].items() for text in texts]


# -- the corpus: what a life lived, gathered under control -----------------------------------------------

def gather(life_path: Path, since: int = 0) -> tuple[list[dict], int, dict]:
    """Read the life's event log from byte `since`: each message heard and the reply the being spoke.
    Returns the items, the new offset, and counts of what was left out and why."""
    log = Path(life_path) / "events.log"
    if not log.exists():
        return [], since, {}
    items, skipped = [], {"too_long": 0, "unanswered": 0, "unreadable": 0}
    heard: str | None = None
    with log.open("rb") as handle:
        handle.seek(since)
        for raw in handle:
            try:
                event = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                skipped["unreadable"] += 1
                continue
            kind = event.get("type")
            if kind == "stage" and event.get("source") == "message":
                if heard is not None:
                    skipped["unanswered"] += 1
                heard = str(event.get("text") or "")
            elif kind == "speech" and event.get("spontaneous") is False and heard is not None:
                said = str(event.get("text") or "")
                if len(heard) + len(said) > MAX_ITEM_CHARS:
                    skipped["too_long"] += 1
                else:
                    items.append({"messages": [{"role": "user", "content": heard}, {"role": "assistant", "content": said}],
                                  "time": event.get("time")})
                heard = None
            elif kind in ("silence",) and heard is not None:
                heard = None
        offset = handle.tell()
    return items, offset, skipped


def held_out(item: dict) -> bool:
    return int(_sha(item_text(item))[:8], 16) % HELD_OUT_EVERY == 0


class EngineLearning:
    """The engine learning of one life: its settings, corpus, checkpoints and ledger."""

    def __init__(self, life_path: Path) -> None:
        self.life_path = Path(life_path)
        self.root = self.life_path / FOLDER
        self._lock = threading.Lock()
        self.progress: dict = {"state": "idle"}
        self._cancel = threading.Event()

    # -- files ---------------------------------------------------------------------------

    def _read(self, name: str, default):
        path = self.root / name
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

    def _write(self, name: str, data) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / name
        partial = path.with_name(path.name + ".part")
        partial.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        partial.replace(path)

    def _append(self, name: str, rows: list[dict]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / name).open("a", encoding="utf-8") as out:
            for row in rows:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _rows(self, name: str) -> list[dict]:
        path = self.root / name
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def record(self, kind: str, **data) -> dict:
        row = {"kind": kind, "time": _now(), "rules": RULES_VERSION, **data}
        self._append("ledger.jsonl", [row])
        return row

    def ledger(self) -> list[dict]:
        return self._rows("ledger.jsonl")

    @property
    def settings(self) -> Settings:
        return Settings.from_dict(self._read("settings.json", {}))

    def configure(self, changes: dict, who: str = "") -> Settings:
        """Change the settings. Turning learning on needs a person's name: that is the approval."""
        current = asdict(self.settings)
        allowed = set(Settings.__dataclass_fields__) - {"approved_by", "approved_utc"}
        moved = {k: v for k, v in (changes or {}).items() if k in allowed and current.get(k) != v}
        if moved.get("enabled") is True:
            if not str(who).strip():
                raise EngineLearningError("turning engine learning on needs the name of the person who approves it")
            current.update(approved_by=str(who).strip()[:80], approved_utc=_now())
        current.update(moved)
        settings = Settings.from_dict(current)
        settings.rank = max(1, min(int(settings.rank), 64))
        settings.max_rank = max(settings.rank, min(int(settings.max_rank), 128))
        settings.steps = max(1, min(int(settings.steps), 2000))
        self._write("settings.json", asdict(settings))
        if moved:
            self.record("settings", changes=moved, who=str(who).strip()[:80] or None)
        return settings

    # -- checkpoints -----------------------------------------------------------------------

    def versions(self) -> list[dict]:
        out = []
        for folder in sorted((self.root / "adapters").glob("a*")):
            manifest = folder / "manifest.json"
            if manifest.exists():
                out.append(json.loads(manifest.read_text(encoding="utf-8")))
        return out

    def active(self, model_id: str | None = None) -> dict | None:
        """The adapter the conversing model must load, or None for the base model alone."""
        pointer = self._read("active.json", {"version": None})
        if not pointer.get("version"):
            return None
        folder = self.root / "adapters" / pointer["version"]
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        if model_id and manifest["base_model_id"] != model_id:
            return None  # an adapter belongs to its base: on another model it means nothing
        gguf = folder / "adapter.gguf"
        if not gguf.is_file():
            return None
        from freewill.learning.gguf_lora import sha256_file
        digest = sha256_file(gguf)
        if digest != manifest["gguf_sha256"]:
            self.record("integrity_failure", version=pointer["version"], expected=manifest["gguf_sha256"], found=digest)
            return None
        return {"version": pointer["version"], "gguf": str(gguf), "sha256": digest, "folder": str(folder)}

    def restore(self, version: str | None, who: str = "") -> dict:
        """Make an earlier checkpoint (or the base alone, with None) the one the being converses with."""
        if version is not None and not (self.root / "adapters" / str(version) / "manifest.json").exists():
            raise EngineLearningError("no such checkpoint")
        before = self._read("active.json", {"version": None}).get("version")
        self._write("active.json", {"version": version, "since": _now()})
        return self.record("restore", before=before, after=version, who=str(who).strip()[:80] or None)

    def _next_version(self) -> str:
        existing = [int(p.name[1:]) for where in ("adapters", "rejected")
                    for p in (self.root / where).glob("a*") if p.name[1:].isdigit()]
        return f"a{(max(existing) + 1) if existing else 1:04d}"

    # -- state for the interface -----------------------------------------------------------------

    def public(self) -> dict:
        state = self._read("state.json", {})
        return {"settings": asdict(self.settings), "active": self._read("active.json", {"version": None}).get("version"),
                "versions": self.versions(), "ledger": self.ledger()[-60:], "progress": self.progress,
                "corpus_items": state.get("train_items", 0), "held_out_items": state.get("held_out_items", 0),
                "pending_items": state.get("pending_items", 0), "rules": RULES_VERSION,
                "thresholds": {"min_gain": MIN_GAIN, "max_forgetting": MAX_FORGETTING,
                               "max_life_forgetting": MAX_LIFE_FORGETTING, "growth_margin": GROWTH_MARGIN,
                               "min_held_out": MIN_HELD_OUT}}

    # -- the corpus ------------------------------------------------------------------------------

    def collect(self) -> dict:
        """Add to the corpus what was lived since the last collection. Held-out items are set aside for good."""
        state = self._read("state.json", {})
        items, offset, skipped = gather(self.life_path, int(state.get("log_offset", 0)))
        known = {row["sha256"] for row in self._rows("corpus.jsonl")} | {row["sha256"] for row in self._rows("heldout.jsonl")}
        fresh_train, fresh_held = [], []
        for item in items:
            digest = _sha(item_text(item))
            if digest in known:
                skipped["duplicate"] = skipped.get("duplicate", 0) + 1
                continue
            known.add(digest)
            row = {**item, "sha256": digest, "collected": _now(), "night": None}
            (fresh_held if held_out(item) else fresh_train).append(row)
        self._append("corpus.jsonl", fresh_train)
        self._append("heldout.jsonl", fresh_held)
        corpus, heldout = self._rows("corpus.jsonl"), self._rows("heldout.jsonl")
        state.update(log_offset=offset, train_items=len(corpus), held_out_items=len(heldout),
                     pending_items=sum(1 for r in corpus if r["night"] is None))
        self._write("state.json", state)
        if fresh_train or fresh_held:
            self.record("corpus", added_train=len(fresh_train), added_held_out=len(fresh_held), skipped=skipped,
                        train_sha256=[r["sha256"] for r in fresh_train], held_out_sha256=[r["sha256"] for r in fresh_held])
        return {"added_train": len(fresh_train), "added_held_out": len(fresh_held), "skipped": skipped}

    # -- one night ---------------------------------------------------------------------------------

    def cancel(self) -> None:
        self._cancel.set()

    def night(self, model: dict, store, *, runtime_check=None, workbench=None, force: bool = False) -> dict:
        """Run one night of engine learning. Returns the ledger row of the decision.

        `store` is the ModelStore; `runtime_check(gguf_path, texts) -> dict` measures the converted
        adapter through llama.cpp (see compare.runtime_losses). `workbench` lets tests pass a toy base."""
        if not self._lock.acquire(blocking=False):
            raise EngineLearningError("a night of engine learning is already running")
        self._cancel.clear()
        try:
            self.progress = {"state": "running", "step": "collect", "started": _now()}
            return self._night(model, store, runtime_check, workbench, force)
        except Exception as error:
            row = self.record("failed", error=f"{type(error).__name__}: {error}")
            self.progress = {"state": "failed", "error": row["error"]}
            raise
        finally:
            if self.progress.get("state") == "running":
                self.progress = {"state": "idle"}
            self._lock.release()

    def _night(self, model, store, runtime_check, workbench, force) -> dict:
        settings = self.settings
        if not settings.enabled and not force:
            raise EngineLearningError("engine learning is off for this life")
        if not model.get("trainable"):
            raise EngineLearningError(f"{model['name']} has no trainable base in the catalogue")
        self.collect()
        corpus, heldout = self._rows("corpus.jsonl"), self._rows("heldout.jsonl")
        new_items = [r for r in corpus if r["night"] is None][:MAX_ITEMS_PER_NIGHT]
        old_items = [r for r in corpus if r["night"] is not None]
        new_held = [r for r in heldout if r["night"] is None]
        old_held = [r for r in heldout if r["night"] is not None]
        if len(new_items) < MIN_TRAIN or len(new_held) + len(old_held) < MIN_HELD_OUT:
            return self.record("skipped", reason="not_enough_lived",
                               new_items=len(new_items), held_out_items=len(new_held) + len(old_held),
                               needs={"train": MIN_TRAIN, "held_out": MIN_HELD_OUT})
        night_id = self._next_version()
        active = self.active(model["id"])
        started = time.monotonic()

        self.progress.update(step="load")
        if workbench is None:
            from freewill.learning.lora import Workbench
            if not store.training_installed(model):
                raise EngineLearningError("the trainable base of this model is not on this computer yet")
            workbench = Workbench(store.base_dir(model), seed=settings.seed)
        bench = workbench
        from freewill.learning.lora import mean_nll
        base_hash_before = bench.base_hash()

        # Replay: a share of earlier training items, chosen by their hashes (reproducible).
        replay = sorted(old_items, key=lambda r: _sha(night_id + r["sha256"]))[:int(len(new_items) * REPLAY_SHARE)]
        rehearsal = []
        if settings.rehearsal:
            pool = sorted(rehearsal_items(), key=lambda r: _sha(night_id + r["text"]))
            rehearsal = pool[:max(1, int(len(new_items) * REHEARSAL_SHARE))]
        train_seq = bench.tokens(new_items + replay + rehearsal, settings.max_len)
        eval_new = bench.tokens(new_held if new_held else old_held, settings.max_len)
        eval_old = bench.tokens(old_held, settings.max_len) if new_held else []
        reference = reference_items()
        eval_ref = bench.tokens(reference, settings.max_len)

        # The adapter in use, and the candidate that starts from it.
        if active:
            bench.load("active", active["folder"])
        bench.delete("candidate")
        if active:
            bench.copy("active", "candidate")
        else:
            bench.fresh("candidate", settings.rank, seed=settings.seed)

        def measure(name):
            return {"life_new": mean_nll(bench.losses(name, eval_new)),
                    "life_old": mean_nll(bench.losses(name, eval_old)) if eval_old else None,
                    "reference": mean_nll(bench.losses(name, eval_ref))}

        self.progress.update(step="measure_before")
        base_scores = measure(None)
        active_scores = measure("active") if active else dict(base_scores)

        self.progress.update(step="train")
        training = bench.train("candidate", train_seq, steps=settings.steps, lr=settings.lr, seed=settings.seed,
                               cancel=self._cancel)
        self.progress.update(step="measure_after")
        candidate_scores = measure("candidate")
        candidates = {"candidate": {"scores": candidate_scores, "training": training,
                                    "rank": bench.ranks["candidate"]["rank"], "parameters": bench.parameters("candidate")}}

        # Structural growth under budget: the same night, with a larger rank, compared with the one above.
        growth = None
        current_rank = bench.ranks["candidate"]["rank"]
        if settings.growth:
            grown_rank = min(current_rank * 2, settings.max_rank)
            source = "active" if active else None
            if grown_rank > current_rank:
                bench.delete("grown")
                if source:
                    bench.copy(source, "grown", rank=grown_rank)
                else:
                    bench.fresh("grown", grown_rank, seed=settings.seed)
                if bench.parameters("grown") <= settings.max_adapter_parameters:
                    self.progress.update(step="train_grown")
                    grown_training = bench.train("grown", train_seq, steps=settings.steps, lr=settings.lr,
                                                 seed=settings.seed, cancel=self._cancel)
                    candidates["grown"] = {"scores": measure("grown"), "training": grown_training, "rank": grown_rank,
                                           "parameters": bench.parameters("grown")}
                else:
                    growth = {"considered": True, "decision": "over_budget", "rank": grown_rank,
                              "parameters": bench.parameters("grown"), "budget": settings.max_adapter_parameters}
                    bench.delete("grown")
            else:
                growth = {"considered": True, "decision": "at_max_rank", "rank": current_rank}

        def verdict(scores):
            reasons = []
            gain = round(active_scores["life_new"] - scores["life_new"], 6)
            forgetting = round(scores["reference"] - base_scores["reference"], 6)
            life_forgetting = None
            if scores["life_old"] is not None and active_scores["life_old"] is not None:
                life_forgetting = round(scores["life_old"] - active_scores["life_old"], 6)
            if gain < MIN_GAIN:
                reasons.append("no_gain_on_held_out")
            if forgetting > MAX_FORGETTING:
                reasons.append("forgets_reference")
            if life_forgetting is not None and life_forgetting > MAX_LIFE_FORGETTING:
                reasons.append("forgets_earlier_nights")
            return {"gain": gain, "forgetting_reference": forgetting, "forgetting_life": life_forgetting,
                    "passes": not reasons, "reasons": reasons}

        for name, entry in candidates.items():
            entry["verdict"] = verdict(entry["scores"])
        chosen = "candidate" if candidates["candidate"]["verdict"]["passes"] else None
        if "grown" in candidates:
            grown, same = candidates["grown"], candidates["candidate"]
            wins = grown["verdict"]["passes"] and (
                not same["verdict"]["passes"] or grown["verdict"]["gain"] - same["verdict"]["gain"] >= GROWTH_MARGIN)
            growth = {"considered": True, "rank_before": current_rank, "rank_after": grown["rank"],
                      "parameters_before": same["parameters"], "parameters_after": grown["parameters"],
                      "gain_same_size": same["verdict"]["gain"], "gain_grown": grown["verdict"]["gain"],
                      "margin_needed": GROWTH_MARGIN, "decision": "accepted" if wins else "rejected",
                      "note": "a larger adapter is kept only if it beats the same night without growth on held-out data"}
            if wins:
                chosen = "grown"

        base_hash_after = bench.base_hash()
        if base_hash_after != base_hash_before:
            raise EngineLearningError("the base weights changed during training: nothing is kept")
        consumed = {r["sha256"] for r in new_items} | {r["sha256"] for r in new_held}
        self._mark_night(consumed, night_id)

        summary = {"night": night_id, "base_model_id": model["id"], "base_parameters": bench.base_parameters,
                   "base_weights_sha256": base_hash_before, "base_weights_unchanged": True,
                   "parent": active["version"] if active else None, "device": bench.device, "dtype": bench.dtype,
                   "train_items_new": len(new_items), "train_items_replayed": len(replay),
                   "train_items_rehearsal": len(rehearsal),
                   "held_out_new": len(new_held), "held_out_earlier": len(old_held),
                   "reference_items": len(reference), "scores_base": base_scores, "scores_active": active_scores,
                   "candidates": candidates, "growth": growth, "settings": asdict(settings),
                   "train_sha256": sorted(r["sha256"] for r in new_items), "replay_sha256": sorted(r["sha256"] for r in replay),
                   "seconds": None}
        if chosen is None:
            for name in candidates:
                bench.delete(name)
            summary["seconds"] = round(time.monotonic() - started, 1)
            self.progress = {"state": "idle", "last": "rejected"}
            return self.record("night", decision="rejected", **summary)

        # Accepted: save, record the change of weights, convert, check, and make it the one in use.
        self.progress.update(step="convert")
        folder = self.root / "adapters" / night_id
        partial = folder.with_name(folder.name + ".part")
        shutil.rmtree(partial, ignore_errors=True)
        bench.save(chosen, partial)
        from freewill.learning.gguf_lora import convert, sha256_file
        architecture = model.get("architecture") or bench.config.get("model_type")
        gguf = convert(partial, partial / "adapter.gguf", architecture)
        delta = bench.delta_norms(chosen)
        (partial / "weights_delta.json").write_text(json.dumps(delta, indent=1) + "\n", encoding="utf-8")
        runtime = None
        if runtime_check is not None and settings.verify_with_runtime:
            self.progress.update(step="runtime_check")
            texts = [bench.render(r) for r in new_held + old_held]
            runtime = runtime_check(partial / "adapter.gguf", texts)
        manifest = {"version": night_id, "base_model_id": model["id"], "base_model_name": model["name"],
                    "base_parameters": bench.base_parameters, "base_weights_sha256": base_hash_before,
                    "parent": active["version"] if active else None, "rank": candidates[chosen]["rank"],
                    "alpha": bench.ranks[chosen]["alpha"], "adapter_parameters": candidates[chosen]["parameters"],
                    "adapter_sha256": bench.adapter_hash(chosen),
                    "safetensors_sha256": sha256_file(partial / "adapter_model.safetensors"),
                    "gguf_sha256": gguf["sha256"], "gguf_tensors": gguf["tensors"], "architecture": architecture,
                    "scores": candidates[chosen]["scores"], "verdict": candidates[chosen]["verdict"],
                    "scores_base": base_scores, "scores_parent": active_scores, "runtime_check": runtime,
                    "delta_total_frobenius": delta["total_frobenius"], "grown": chosen == "grown",
                    "created": _now(), "rules": RULES_VERSION}
        (partial / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
        partial.replace(folder)
        if runtime is not None and (runtime.get("ran") is False or runtime.get("adapter_loaded") is False):
            # Rule 5: when the check is asked for, an adapter llama.cpp could not measure is not put in use.
            # It is kept aside for inspection, never among the checkpoints that can be restored.
            aside = self.root / "rejected" / night_id
            aside.parent.mkdir(parents=True, exist_ok=True)
            shutil.rmtree(aside, ignore_errors=True)
            folder.replace(aside)
            summary["seconds"] = round(time.monotonic() - started, 1)
            self.progress = {"state": "idle", "last": "rejected"}
            return self.record("night", decision="rejected_by_runtime", runtime_check=runtime, **summary)
        self._write("active.json", {"version": night_id, "since": _now()})
        for name in list(candidates) + (["active"] if active else []):
            bench.delete(name)
        summary["seconds"] = round(time.monotonic() - started, 1)
        self.progress = {"state": "idle", "last": "accepted"}
        return self.record("night", decision="accepted", version=night_id, chosen=chosen,
                           adapter_sha256=manifest["adapter_sha256"], gguf_sha256=gguf["sha256"],
                           delta_total_frobenius=delta["total_frobenius"], runtime_check=runtime, **summary)

    def _mark_night(self, consumed: set[str], night_id: str) -> None:
        for name in ("corpus.jsonl", "heldout.jsonl"):
            rows = self._rows(name)
            for row in rows:
                if row["sha256"] in consumed and row["night"] is None:
                    row["night"] = night_id
            path = self.root / name
            partial = path.with_name(path.name + ".part")
            partial.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
            partial.replace(path)
        state = self._read("state.json", {})
        state["pending_items"] = sum(1 for r in self._rows("corpus.jsonl") if r["night"] is None)
        self._write("state.json", state)
