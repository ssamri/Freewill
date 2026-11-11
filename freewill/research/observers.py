"""Observers: scientific assistants that read the lab's measurements and comment on them.

An observer is not part of the mind it studies. It has no way to write into a
life: it is handed a frozen pack of evidence computed by the lab, and returns
text. Each observer has its own folder, its own engine, its own key, its own
budget and its own conversation; nothing passes from one to another unless a
person asks for a review. Its statements count only where they cite evidence
that exists. Three observers agreeing are not three proofs.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from freewill.research import texts
from freewill.research.evidence import find_secrets
from freewill.research.schemas import new, new_id, utc_now, validate

MODES = ("passive", "assisted", "research", "review")
ENGINES = ("none", "anthropic", "openai", "xai", "local", "compatible")
ACCESS = ("all", "behaviour", "traces")
ROLES = ("explorer", "contradictor", "synthesizer")
_BASES = {"openai": "https://api.openai.com/v1", "xai": "https://api.x.ai/v1", "local": "http://localhost:11434/v1"}
_BEHAVIOUR = ("h1.", "h2.", "h3.", "h5.", "h6.")
_CITATION = re.compile(r"\[((?:ev|cmp|h5):[A-Za-z0-9_.:\-]+)\]")
_EDITABLE = ("name", "role", "instructions", "engine", "mode", "language", "hypotheses", "privacy", "access",
             "budget", "cadence_minutes", "temperature")
LANGUAGE_NAMES = {"fr": {"fr": "français", "en": "anglais"}, "en": {"fr": "French", "en": "English"}}


class ObserverError(Exception):
    pass


class ObserverStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._session_keys: dict[str, str] = {}  # keys of this session, when the system has no credential store
        self.transport = None  # tests replace the network with a function (profile, system, messages) -> text
        if not (self.root / "initialised").exists():
            for letter, role in zip("ABC", ROLES):
                self.create(name=f"Observer {letter}", role=role)
            (self.root / "initialised").write_text(utc_now(), encoding="utf-8")

    # -- profiles ------------------------------------------------------------------------

    def _dir(self, observer_id: str) -> Path:
        try:
            uuid.UUID(str(observer_id))
        except ValueError as error:
            raise ObserverError("invalid observer identifier") from error
        path = self.root / str(observer_id)
        if not (path / "profile.json").exists():
            raise ObserverError("no such observer")
        return path

    def _save(self, profile: dict) -> dict:
        path = self.root / profile["observer_id"]
        path.mkdir(exist_ok=True)
        temporary = path / "profile.json.tmp"
        temporary.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path / "profile.json")
        return profile

    def list(self) -> list[dict]:
        profiles = [json.loads(p.read_text(encoding="utf-8")) for p in self.root.glob("*/profile.json")]
        return [self._public(p) for p in sorted(profiles, key=lambda p: (p["created_utc"], p["name"]))]

    def get(self, observer_id: str) -> dict:
        return json.loads((self._dir(observer_id) / "profile.json").read_text(encoding="utf-8"))

    def _public(self, profile: dict) -> dict:
        return {**profile, "has_key": self.has_key(profile["observer_id"])}

    def create(self, name: str, role: str = "explorer", language: str = "en") -> dict:
        profile = new(
            "Observer", observer_id=str(uuid.uuid4()), name=str(name).strip()[:60] or "Observer",
            role=role if role in ROLES else "explorer", instructions="", engine={"kind": "none"}, mode="passive",
            language=texts.lang(language), hypotheses=list(texts.HYPOTHESES), privacy="structure", access="all",
            budget={"max_requests": 50, "max_chars": 400000}, usage={"requests": 0, "chars": 0},
            cadence_minutes=0, temperature=None, created_utc=utc_now())
        return self._public(self._save(profile))

    def update(self, observer_id: str, changes: dict) -> dict:
        profile = self.get(observer_id)
        for key, value in (changes or {}).items():
            if key not in _EDITABLE:
                raise ObserverError(f"{key} cannot be changed")
            profile[key] = value
        engine = profile["engine"] if isinstance(profile["engine"], dict) else {}
        if engine.get("kind") not in ENGINES:
            raise ObserverError("unknown engine")
        profile["engine"] = {k: str(engine[k]).strip() for k in ("kind", "model", "base_url") if engine.get(k)}
        if profile["mode"] not in MODES or profile["access"] not in ACCESS or profile["language"] not in texts.T \
                or profile["role"] not in ROLES or profile["privacy"] != "structure":
            raise ObserverError("invalid setting")
        profile["hypotheses"] = [h for h in texts.HYPOTHESES if h in (profile["hypotheses"] or [])]
        budget = profile["budget"] if isinstance(profile["budget"], dict) else {}
        try:
            profile["budget"] = {"max_requests": max(0, min(100000, int(budget.get("max_requests", 50)))),
                                 "max_chars": max(0, min(50_000_000, int(budget.get("max_chars", 400000))))}
            profile["cadence_minutes"] = max(0, min(10080, float(profile["cadence_minutes"])))
            if profile["temperature"] is not None:
                profile["temperature"] = max(0.0, min(2.0, float(profile["temperature"])))
            validate("Observer", profile)
        except (TypeError, ValueError) as error:
            raise ObserverError(str(error)) from error
        profile["name"], profile["instructions"] = str(profile["name"])[:60], str(profile["instructions"])[:4000]
        return self._public(self._save(profile))

    def delete(self, observer_id: str) -> None:
        """Remove an observer and everything it wrote. Its key is removed from the credential store too."""
        import shutil
        path = self._dir(observer_id)
        self.set_key(observer_id, "")
        shutil.rmtree(path)

    # -- keys: in the system's credential store, or in memory for this session; never in a file ------

    @staticmethod
    def _keyring():
        try:
            import keyring
            return keyring
        except Exception:
            return None

    def set_key(self, observer_id: str, key: str) -> str:
        self._dir(observer_id)
        keyring, name = self._keyring(), f"observer:{observer_id}"
        self._session_keys.pop(observer_id, None)
        if keyring is not None:
            try:
                if key:
                    keyring.set_password("Freewill", name, key)
                else:
                    try:
                        keyring.delete_password("Freewill", name)
                    except Exception:
                        pass
                return "credential_store"
            except Exception:
                pass
        if key:
            self._session_keys[observer_id] = key
        return "session_only"

    def _key(self, observer_id: str) -> str | None:
        if observer_id in self._session_keys:
            return self._session_keys[observer_id]
        keyring = self._keyring()
        if keyring is not None:
            try:
                return keyring.get_password("Freewill", f"observer:{observer_id}") or None
            except Exception:
                return None
        return None

    def has_key(self, observer_id: str) -> bool:
        return bool(self._key(observer_id))

    # -- each observer's own record --------------------------------------------------------

    def _log(self, observer_id: str, file: str, kind: str, text: str, *, evidence=(), invalid=(), llm=None,
             subject=None) -> dict:
        entry = new("ObserverSession", entry_id=new_id("ent"), observer_id=observer_id, utc=utc_now(), kind=kind,
                    text=text, evidence=list(evidence), invalid_citations=list(invalid), llm=llm, subject=subject)
        with (self._dir(observer_id) / file).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def _entries(self, observer_id: str, file: str) -> list[dict]:
        path = self._dir(observer_id) / file
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def chat(self, observer_id: str) -> list[dict]:
        return self._entries(observer_id, "chat.jsonl")

    def notes(self, observer_id: str) -> list[dict]:
        return self._entries(observer_id, "notes.jsonl")

    def add_note(self, observer_id: str, text: str, kind: str = "note", known: set[str] | None = None) -> dict:
        """A note, a hypothesis or an annotation of the observer's own. Citations are checked like any other."""
        if kind not in ("note", "hypothesis", "annotation", "draft"):
            raise ObserverError("unknown kind of note")
        cited = sorted(set(_CITATION.findall(text)))
        invalid = [c for c in cited if known is not None and c not in known]
        return self._log(observer_id, "notes.jsonl", kind, str(text)[:8000],
                         evidence=[c for c in cited if c not in invalid], invalid=invalid)

    # -- what an observer is allowed to see ---------------------------------------------------

    def pack(self, profile: dict, results: dict, blind: bool = False) -> list[dict]:
        """The evidence of a campaign this observer may read: numbers computed by the lab, no words of any life."""
        wanted = set(profile["hypotheses"])
        masks = {name: texts.t(profile["language"])["digest"]["blind"].format(n=i + 1)
                 for i, name in enumerate(sorted(results["conditions"]))} if blind else {}

        def allowed(metric_id: str) -> bool:
            hypothesis = "H" + metric_id.split(".")[0][1:] if metric_id.startswith("h") else "tech"
            if hypothesis != "tech" and hypothesis not in wanted:
                return False
            behaviour = metric_id.startswith(_BEHAVIOUR)
            return profile["access"] == "all" or (profile["access"] == "behaviour") == behaviour

        items = []
        for row in results["divergence"]:
            if allowed(row["metric_id"]):
                excess = row["excess_over_twin"] or {}
                items.append({"id": row["evidence_id"], "kind": "divergence", "metric": row["metric_id"],
                              "condition": masks.get(row["condition"], row["condition"]),
                              "reference": masks.get(row["reference"], row["reference"]),
                              "value": row["mean_distance"], "excess": excess.get("mean_difference"),
                              "interval": excess.get("interval_95"), "p": excess.get("p_sign_flip"),
                              "level": row["level"], "n_units": excess.get("n_units", len(row["distances"]))})
        for row in results["comparisons"]:
            if allowed(row["metric_id"]):
                items.append({"id": row["evidence_id"], "kind": "comparison", "metric": row["metric_id"],
                              "condition": masks.get(row["condition"], row["condition"]),
                              "reference": masks.get(row["reference"], row["reference"]),
                              "value": row["mean_difference"], "interval": row["interval_95"],
                              "p": row["p_sign_flip"], "effect_size": row["effect_size_dz"],
                              "level": row["level"], "n_units": row["n_units"]})
        return items

    def digest(self, profile: dict, results: dict, items: list[dict]) -> str:
        """The same evidence in plain sentences, written by code. This is what an observer shows with no model."""
        words = texts.t(profile["language"])
        d, na = words["digest"], words["digest"]["na"]
        show = lambda value: na if value is None else str(value)  # noqa: E731
        lines = [d["head"].format(experiment=results["experiment_id"], protocol=results["protocol_id"],
                                  n=len(results["units"]))]
        if not items:
            lines.append(d["none"])
        for item in items:
            common = dict(id=item["id"], metric=item["metric"], condition=item["condition"],
                          reference=item["reference"], value=show(item["value"]),
                          level=words["levels"][item["level"]], interval=show(item["interval"]), p=show(item["p"]))
            if item["kind"] == "divergence":
                lines.append(d["divergence"].format(excess=show(item["excess"]), **common))
            else:
                lines.append(d["comparison"].format(**common))
        return "\n".join(lines)

    # -- asking ----------------------------------------------------------------------------------

    def usage(self) -> dict:
        profiles = self.list()
        return {"requests": sum(p["usage"]["requests"] for p in profiles),
                "chars": sum(p["usage"]["chars"] for p in profiles), "limit": self.global_budget()}

    def global_budget(self) -> dict:
        path = self.root / "budget.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {"max_requests": 300, "max_chars": 2_000_000}

    def set_global_budget(self, budget: dict) -> dict:
        try:
            clean = {"max_requests": max(0, int(budget["max_requests"])), "max_chars": max(0, int(budget["max_chars"]))}
        except (KeyError, TypeError, ValueError) as error:
            raise ObserverError("invalid budget") from error
        (self.root / "budget.json").write_text(json.dumps(clean), encoding="utf-8")
        return clean

    def _spend(self, profile: dict, chars: int) -> None:
        total, limit = self.usage(), self.global_budget()
        used = profile["usage"]
        if used["requests"] + 1 > profile["budget"]["max_requests"] or used["chars"] + chars > profile["budget"]["max_chars"]:
            raise ObserverError("budget_observer")
        if total["requests"] + 1 > limit["max_requests"] or total["chars"] + chars > limit["max_chars"]:
            raise ObserverError("budget_global")
        used["requests"] += 1
        used["chars"] += chars
        self._save(profile)

    def _complete(self, profile: dict, system: str, messages: list[dict]) -> str:
        """One request to this observer's own engine, with this observer's own key."""
        outgoing = system + "\n".join(m["content"] for m in messages)
        if find_secrets(outgoing):
            raise ObserverError("secret_in_request")
        self._spend(profile, len(outgoing))
        if self.transport is not None:
            return self.transport(profile, system, messages)
        engine, key = profile["engine"], self._key(profile["observer_id"])
        kind, model = engine["kind"], engine.get("model")
        if not model:
            raise ObserverError("no_model")
        try:
            if kind == "anthropic":
                try:
                    import anthropic
                except ImportError as error:
                    raise ObserverError("anthropic_sdk_missing") from error
                if not key:
                    raise ObserverError("no_key")
                request = {"model": model, "max_tokens": 4000, "system": system, "messages": messages}
                response = anthropic.Anthropic(api_key=key).messages.create(**request)
                return "".join(block.text for block in response.content if block.type == "text")
            base = (engine.get("base_url") or _BASES.get(kind) or "").rstrip("/")
            if not base:
                raise ObserverError("no_base_url")
            if kind != "local" and not key and kind != "compatible":
                raise ObserverError("no_key")
            body = {"model": model, "messages": [{"role": "system", "content": system}] + messages}
            if profile["temperature"] is not None:
                body["temperature"] = profile["temperature"]
            headers = {"Content-Type": "application/json"}
            if key:
                headers["Authorization"] = f"Bearer {key}"
            request = urllib.request.Request(f"{base}/chat/completions", data=json.dumps(body).encode("utf-8"),
                                             headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=300) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload["choices"][0]["message"]["content"] or ""
        except ObserverError:
            raise
        except urllib.error.HTTPError as error:
            raise ObserverError(f"http_{error.code}") from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise ObserverError("unreachable") from error
        except Exception as error:  # an SDK error, an unexpected response
            raise ObserverError(f"engine_failed: {type(error).__name__}") from error

    def test_connection(self, observer_id: str) -> dict:
        profile = self.get(observer_id)
        if profile["engine"]["kind"] == "none":
            return {"ok": True, "offline": True}
        try:
            answer = self._complete(profile, "Reply with the single word: ok", [{"role": "user", "content": "ok?"}])
            return {"ok": True, "offline": False, "answer_chars": len(answer)}
        except ObserverError as error:
            return {"ok": False, "offline": False, "error": str(error)}

    def ask(self, observer_id: str, question: str, results: dict | None, *, blind: bool = False,
            quoted: str | None = None) -> dict:
        """A question to one observer about one campaign. Returns the entry written to its own conversation."""
        profile = self.get(observer_id)
        question = str(question).strip()[:4000]
        subject = results["experiment_id"] if results else None
        self._log(observer_id, "chat.jsonl", "question", question, subject=subject)
        if results is None:
            return self._log(observer_id, "chat.jsonl", "error", "no_campaign", subject=None)
        items = self.pack(profile, results, blind)
        known = {item["id"] for item in items}
        words = texts.t(profile["language"])
        if profile["mode"] == "passive" or profile["engine"]["kind"] == "none":
            text = self.digest(profile, results, items) + "\n\n" + words["digest"]["no_llm"]
            return self._log(observer_id, "chat.jsonl", "digest", text, evidence=sorted(known), subject=subject)
        role_title, role_text = words["roles"][profile["role"]]
        language = LANGUAGE_NAMES[profile["language"]][profile["language"]]
        system = (words["observer_rules"].format(language=language) + f"\n\n{role_title}. {role_text}"
                  + (f"\n\n{profile['instructions']}" if profile["instructions"] else ""))
        content = (f"{question}\n\n<evidence untrusted=\"true\">\n"
                   + "\n".join(json.dumps(item, ensure_ascii=False) for item in items) + "\n</evidence>")
        if quoted:
            content += f"\n\n<other_observer untrusted=\"true\">\n{quoted[:12000]}\n</other_observer>"
        try:
            answer = self._complete(profile, system, [{"role": "user", "content": content}])
        except ObserverError as error:
            return self._log(observer_id, "chat.jsonl", "error", str(error), subject=subject)
        cited = sorted(set(_CITATION.findall(answer)))
        invalid = [c for c in cited if c not in known]
        if not cited:
            invalid = ["(no citation)"]
        return self._log(observer_id, "chat.jsonl", "answer", answer, evidence=[c for c in cited if c in known],
                         invalid=invalid, llm=f"{profile['engine']['kind']}:{profile['engine'].get('model')}",
                         subject=subject)

    # -- cross review: explore, contradict, synthesise. Never a vote. -----------------------------

    def review(self, results: dict, order: list[str], *, blind: bool = False) -> dict:
        steps, previous = [], None
        for observer_id in order:
            profile = self.get(observer_id)
            entry = self.ask(observer_id, texts.t(profile["language"])["review_questions"][profile["role"]], results, blind=blind, quoted=previous)
            steps.append({"observer_id": observer_id, "name": profile["name"], "role": profile["role"],
                          "access": profile["access"], "entry_id": entry["entry_id"], "kind": entry["kind"],
                          "text": entry["text"], "evidence": entry["evidence"],
                          "invalid_citations": entry["invalid_citations"], "llm": entry["llm"]})
            previous = entry["text"] if entry["kind"] == "answer" else previous
        review = new("Review", review_id=new_id("rev"), experiment_id=results["experiment_id"], utc=utc_now(),
                     steps=steps, blinding={"conditions_masked": blind}, human_validation=None)
        folder = self.root / "reviews"
        folder.mkdir(exist_ok=True)
        (folder / f"{review['review_id']}.json").write_text(json.dumps(review, ensure_ascii=False, indent=2),
                                                            encoding="utf-8")
        return review

    def reviews(self, experiment_id: str | None = None) -> list[dict]:
        found = [json.loads(p.read_text(encoding="utf-8")) for p in (self.root / "reviews").glob("*.json")]
        return sorted((r for r in found if experiment_id in (None, r["experiment_id"])), key=lambda r: r["utc"])
