"""The Research Lab behind the local service.

Same protections as the rest of the service: loopback only, session token,
Host check. These routes read measurements and manage the lab's own files.
None of them can write into a life: the only contact with a real life is
copying its state, under its lock, to make the checkpoint of a campaign.
"""

from __future__ import annotations

import webbrowser

from freewill import learning
from freewill.research import metrics, reports, texts
from freewill.research.experiments import HISTORIES, Lab, LabError
from freewill.research.observers import ACCESS, ENGINES, MODES, ROLES, ObserverError, ObserverStore


class LabApi:
    def __init__(self, app) -> None:
        self.app = app
        self.lab = Lab(app.lives_dir.parent / "lab")
        self.observers = ObserverStore(self.lab.root / "observers")

    # -- reading ---------------------------------------------------------------------------

    def home(self, language: str) -> dict:
        words = texts.t(language)
        status = self.lab.hypothesis_status()
        hypotheses = []
        for h in texts.hypotheses(language):
            verdict = status["verdicts"].get(h["id"])
            measured = status["measured"].get(h["id"], [])
            research = verdict["verdict"] if verdict else ("measured" if measured else "not_measured")
            hypotheses.append({**h, "research": research, "research_label": words["research"][research],
                               "campaigns": measured, "verdict": verdict,
                               "metrics": [{**d, "level_label": words["levels"][d["level"]],
                                            "not_computable": words["reasons"].get(metrics.NOT_COMPUTABLE.get(d["metric_id"], ""))}
                                           for d in metrics.DEFINITIONS.values() if d["hypothesis"] == h["id"]]})
        protocols = [{**p, "title_label": p["title"][texts.lang(language)],
                      "reason": words["reasons"].get(p.get("notes") or "")} for p in self.lab.protocols()]
        experiments = self.lab.experiments()
        alerts = []
        if not any(e["status"] == "done" for e in experiments):
            alerts.append("no_campaign")
        if any(e["anomalies"] for e in experiments):
            alerts.append("anomalies")
        alerts.append("simulated_engine")
        return {"hypotheses": hypotheses, "protocols": protocols, "experiments": experiments,
                "observers": self.observers.list(), "usage": self.observers.usage(), "alerts": alerts,
                "learning": learning.capabilities(self.app.models.root), "histories": sorted(HISTORIES),
                "options": {"modes": MODES, "engines": ENGINES, "access": ACCESS, "roles": ROLES},
                "awake": self.app.runner.life.name if self.app.runner else None}

    def get(self, path: str, query: dict):
        one = lambda name: (query.get(name) or [""])[0]  # noqa: E731
        if path == "/api/lab/home":
            return self.home(one("lang"))
        if path == "/api/lab/experiment":
            return {"experiment": self.lab.experiment(one("id")), "results": self.lab.results(one("id")),
                    "reviews": self.observers.reviews(one("id"))}
        if path == "/api/lab/observer":
            return {"profile": self.observers._public(self.observers.get(one("id"))),
                    "chat": self.observers.chat(one("id")), "notes": self.observers.notes(one("id"))}
        if path == "/api/lab/reports":
            return {"reports": reports.list_reports(self.lab)}
        if path == "/api/lab/learning":
            versions = learning.model_versions(self.app.models)
            words = texts.t(one("lang"))["learning"]
            found = learning.capabilities(self.app.models.root)
            runner = self.app.runner
            return {"capabilities": found, "versions": versions, "modules": runner.modules() if runner else None,
                    "manifests": [learning.manifest_for(v) for v in versions],
                    "message": words["own_ready"] if found["torch"] else words["unavailable"],
                    "growth": words["growth"],
                    "reasons": [words["reasons"][r].format(need=found["min_free_memory_gb"]) for r in found["reasons"]]}
        return None

    # -- acting on the lab's own files -------------------------------------------------------

    def post(self, path: str, body: dict):
        lab, observers = self.lab, self.observers
        if path == "/api/lab/protocol/duplicate":
            return lab.duplicate_protocol(str(body.get("id")), str(body.get("version")), str(body.get("new_version")))
        if path == "/api/lab/protocol/save":
            return lab.save_protocol(body.get("protocol") or {})
        if path == "/api/lab/experiment/create":
            source = None
            if body.get("from_life") is True:
                runner = self.app.require_runner()
                with runner._living:  # between two moments: the copy is of one consistent state
                    return lab.create_experiment(str(body.get("protocol_id")), str(body.get("version")),
                                                 approved_by_human=body.get("approved") is True,
                                                 source_life=runner.life.path)
            return lab.create_experiment(str(body.get("protocol_id")), str(body.get("version")),
                                         approved_by_human=body.get("approved") is True, source_life=source)
        if path == "/api/lab/experiment/start":
            return lab.start(str(body.get("id")))
        if path == "/api/lab/experiment/cancel":
            return lab.cancel(str(body.get("id")))
        if path == "/api/lab/experiment/delete":
            lab.delete_experiment(str(body.get("id")))
            return {"ok": True}
        if path == "/api/lab/verdict":
            return lab.set_verdict(str(body.get("hypothesis")), body.get("verdict"), str(body.get("who") or ""),
                                   body.get("experiment_id"))
        if path == "/api/lab/observer/create":
            return observers.create(str(body.get("name") or ""), str(body.get("role") or "explorer"),
                                    str(body.get("language") or "en"))
        if path == "/api/lab/observer/update":
            return observers.update(str(body.get("id")), body.get("changes") or {})
        if path == "/api/lab/observer/delete":
            observers.delete(str(body.get("id")))
            return {"ok": True}
        if path == "/api/lab/observer/key":
            return {"stored": observers.set_key(str(body.get("id")), str(body.get("key") or "").strip())}
        if path == "/api/lab/observer/test":
            return observers.test_connection(str(body.get("id")))
        if path == "/api/lab/observer/ask":
            results = lab.results(str(body.get("experiment_id"))) if body.get("experiment_id") else None
            return observers.ask(str(body.get("id")), str(body.get("question") or ""), results,
                                 blind=body.get("blind") is True)
        if path == "/api/lab/observer/note":
            results = lab.results(str(body.get("experiment_id"))) if body.get("experiment_id") else None
            return observers.add_note(str(body.get("id")), str(body.get("text") or ""), str(body.get("kind") or "note"),
                                      set(results["evidence"]) if results else None)
        if path == "/api/lab/budget":
            return observers.set_global_budget(body)
        if path == "/api/lab/review":
            results = lab.results(str(body.get("experiment_id")))
            if results is None:
                raise LabError("this campaign has no results yet")
            order = [str(i) for i in (body.get("order") or [])][:8]
            return observers.review(results, order, blind=body.get("blind") is True)
        if path == "/api/lab/report/build":
            experiment_id = str(body.get("experiment_id"))
            return reports.build(lab, experiment_id, str(body.get("language") or "en"),
                                 author=str(body.get("author") or "Freewill Research Lab"),
                                 reviews=observers.reviews(experiment_id), with_words=body.get("with_words") is True)
        if path == "/api/lab/report/validate":
            return reports.validate_report(lab, str(body.get("report_id")), str(body.get("who") or ""))
        if path == "/api/lab/report/reveal":
            folder = lab.root / "reports"  # a fixed folder of the lab: no path is taken from the request
            webbrowser.open(folder.as_uri())
            return {"ok": True}
        if path == "/api/lab/learning/action":
            action = str(body.get("action"))
            if action not in ("learner_rollback", "own_rollback", "own_sample"):
                raise LabError("unknown action")
            return self.app.require_runner().module_action(action, str(body.get("prompt") or ""))
        if path == "/api/lab/learning/request":
            runner = self.app.require_runner()
            return learning.request_job(runner.life.name, str(body.get("method") or "lora"),
                                        approved_by_human=body.get("approved") is True,
                                        models_dir=self.app.models.root)
        return None


LAB_ERRORS = (LabError, ObserverError, ValueError, OSError)
