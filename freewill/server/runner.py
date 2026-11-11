"""Keeps one being alive in a background thread.

The interface can be closed without the being ceasing to live for as long as
this process runs; the runner owns the loop, the interface only watches.
"""

from __future__ import annotations

import json
import queue
import threading
import time
from collections import deque
from pathlib import Path

from freewill.core.events import Event
from freewill.core.kernel.constitution import founding_questions
from freewill.core.life import Life
from freewill.core.loop import Being
from freewill.engines.base import EngineError, make_engine

HISTORY = 1500  # events kept in memory for an interface that connects late


class Runner:
    def __init__(self, life_path: Path, *, tempo: float | None = None, thoughts_per_hour: int | None = None,
                 engine_options: dict | None = None) -> None:
        self.life = Life(life_path)
        # may raise EngineError
        self.engine = make_engine({**self.life.identity.get("engine", {}), **(engine_options or {})})

        self._events: deque[dict] = deque(maxlen=HISTORY)
        self._seq = 0
        self._changed = threading.Condition()
        self._incoming: "queue.Queue[str]" = queue.Queue()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._living = threading.Lock()  # held while a moment is being lived
        self.paused_reason: str | None = None
        self._sleep_now = False
        self._activity = "waiting"
        self.snapshot: dict = {}

        self._load_history()
        self.being = Being(self.life, self.engine)
        self.being.events.subscribe(self._on_event)
        # The rhythm is kept with the life, unless whoever starts it asks for another.
        research = self.being.research
        self.tempo = research.tempo if tempo is None else tempo
        self.thoughts_per_hour = research.thoughts_per_hour if thoughts_per_hour is None else thoughts_per_hour
        self._refresh_snapshot()

    # -- events ----------------------------------------------------------------

    def _load_history(self) -> None:
        log = self.life.path / "events.log"
        if not log.exists():
            return
        with log.open(encoding="utf-8") as handle:
            for line in deque(handle, maxlen=HISTORY):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._push({"type": record.pop("type", "?"), "time": record.pop("time", ""),
                            "data": record, "past": True})

    def _push(self, record: dict) -> None:
        with self._changed:
            self._seq += 1
            record["seq"] = self._seq
            self._events.append(record)
            self._changed.notify_all()

    def _on_event(self, event: Event) -> None:
        # Publish the current mode before waking an interface waiting for this
        # event. Updating these fields needs no scan of the memories on disk.
        with self._changed:
            if event.type == "sleep":
                self._set_activity("sleeping")
            elif event.type == "stage":
                self._set_activity("thinking")
            elif event.type == "rest":
                # Sleep ended; the tick still has to finish its persistence.
                self._set_activity("thinking")
            self._push({"type": event.type, "time": event.time, "data": event.data})

    def _set_activity(self, activity: str) -> None:
        with self._changed:
            if self._activity == activity:
                return
            self._activity = activity
            self.snapshot = {**self.snapshot, "activity": activity,
                             "sleeping": activity == "sleeping"}
            self._changed.notify_all()

    def events_since(self, seq: int, timeout: float = 15.0) -> list[dict]:
        """Events after `seq`. Blocks up to `timeout` seconds if there are none yet."""
        with self._changed:
            if self._seq <= seq:
                # Wake for a new event or a change of mode (thinking, sleeping,
                # paused); a refreshed snapshot alone is not a reason to answer.
                activity = self._activity
                self._changed.wait_for(
                    lambda: self._seq > seq or self._activity != activity, timeout)
            return [record for record in self._events if record["seq"] > seq]

    # -- life ------------------------------------------------------------------

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="freewill-life", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=30)
        close = getattr(self.engine, "close", None)
        if close:
            close()

    def hear(self, text: str, attachments: list[dict] | None = None) -> None:
        self._incoming.put((text, attachments or []))
        self._wake.set()

    def sleep(self) -> None:
        """The person suggests sleep. It happens at the next moment."""
        self._sleep_now = True
        self._wake.set()

    # -- H7: the computed affective state -------------------------------------------

    def affect(self) -> dict:
        """The computed state, its history and what produced it. A measurement, not a feeling."""
        if not self._living.acquire(timeout=5):
            raise TimeoutError("the being is in the middle of a moment")
        try:
            return json.loads(json.dumps(self.being.affect.public()))
        finally:
            self._living.release()

    def set_affect(self, enabled: bool | None = None, config: dict | None = None) -> dict:
        """Switch the research mode, or change its bounded settings, between two moments."""
        if not self._living.acquire(timeout=60):
            raise TimeoutError("the being is in the middle of a moment")
        try:
            if config:
                self.being.affect.configure(config)
            if enabled is not None and enabled != self.being.affect.enabled:
                self.being.set_affect(enabled)
            self._refresh_snapshot()
            return json.loads(json.dumps(self.being.affect.public()))
        finally:
            self._living.release()

    def configure(self, *, tempo: float | None = None, thoughts_per_hour: int | None = None) -> None:
        changes = {}
        if tempo is not None:
            changes["tempo"] = float(tempo)
        if thoughts_per_hour is not None:
            changes["thoughts_per_hour"] = int(thoughts_per_hour)
        self.set_research(changes)

    def research(self) -> dict:
        return self.being.research.public()

    def modules(self) -> dict:
        """The research modules of this life (H8, H10, H4) as they are now. None when a module is switched off."""
        if not self._living.acquire(timeout=5):
            raise TimeoutError("the being is in the middle of a moment")
        try:
            being = self.being
            return json.loads(json.dumps({
                "metacognition": being.monitor.public() if being.monitor else None,
                "sandbox": being.agency.public() if being.agency else None,
                "learner": being.adapter.public() if being.adapter else None,
                "own_model": being.own.public() if being.own else None}))
        finally:
            self._living.release()

    def module_action(self, action: str, prompt: str = "") -> dict:
        """A person's controls over what was learned: go back to earlier weights, or look at what the network writes."""
        if not self._living.acquire(timeout=60):
            raise TimeoutError("the being is in the middle of a moment")
        try:
            being = self.being
            if action == "learner_rollback" and being.adapter:
                being.adapter.rollback()
                return {"ok": True}
            if action == "own_rollback" and being.own:
                return {"ok": being.own.rollback()}
            if action == "own_sample" and being.own:
                return {"text": being.own.sample(prompt[:200])}
            return {"ok": False}
        finally:
            self._living.release()

    def set_research(self, changes: dict | None = None, reset: bool = False) -> dict:
        """Switch mechanisms of the life loop on or off, between two moments."""
        if not self._living.acquire(timeout=60):
            raise TimeoutError("the being is in the middle of a moment")
        try:
            self.being.set_research(changes, reset)
            self.tempo = self.being.research.tempo
            self.thoughts_per_hour = self.being.research.thoughts_per_hour
            self._refresh_snapshot()
        finally:
            self._living.release()
        self._wake.set()
        return self.research()

    def _run(self) -> None:
        thought_times: list[float] = []
        next_thought = time.monotonic() + 1.0
        backoff = 0.0
        while not self._stop.is_set():
            self._wake.wait(timeout=max(0.05, next_thought - time.monotonic()))
            self._wake.clear()
            if self._stop.is_set():
                break
            spoken_to = False
            while not self._incoming.empty():
                self.being.hear(*self._incoming.get())
                spoken_to = True
            if self._sleep_now:
                self._sleep_now = False
                self.being.sleep_requested = True
                next_thought = time.monotonic()
            if spoken_to:
                self.paused_reason = None
                next_thought = min(next_thought, time.monotonic() + backoff)
            now = time.monotonic()
            if now < next_thought:
                continue
            asked = bool(self.being.inbox) or self.being.sleep_requested
            if self.paused_reason and not asked:
                self._set_activity("paused")
                next_thought = now + 5
                continue
            # Hourly budget: spontaneous thinking pauses; being spoken to still gets through.
            thought_times = [stamp for stamp in thought_times if now - stamp < 3600]
            if len(thought_times) >= self.thoughts_per_hour and not asked:
                self._set_activity("budget")
                next_thought = now + 5
                continue
            self._set_activity("thinking")
            try:
                with self._living:
                    lived = self.being.tick()
                if lived is not None:
                    thought_times.append(now)
                backoff = 0.0
            except EngineError as error:
                if error.retryable:
                    backoff = min(300.0, max(10.0, backoff * 2))
                else:
                    # Stop thinking until the person speaks again or changes a setting.
                    self.paused_reason = str(error)
            except Exception as error:  # never let the life thread die silently
                self.paused_reason = f"{type(error).__name__}: {error}"
                self._push({"type": "engine_error", "time": "", "data": {"message": self.paused_reason}})
            if self.paused_reason:
                activity = "paused"
            elif backoff:
                activity = "retrying"
            elif (len(thought_times) >= self.thoughts_per_hour
                  and not self.being.inbox and not self.being.sleep_requested):
                activity = "budget"
            else:
                activity = "waiting"
            self._set_activity(activity)
            self._refresh_snapshot()
            next_thought = time.monotonic() + self.tempo + backoff

    # -- what the interface sees -------------------------------------------------

    def _refresh_snapshot(self) -> None:
        life, being = self.life, self.being
        snapshot = {
            "awake": True,
            "name": life.name,
            "age": life.age(),
            "born": life.identity["born"],
            "language": life.language,
            "gender": life.identity.get("gender"),
            "interlocutor": life.identity.get("interlocutor"),
            "engine": {**life.identity.get("engine", {}), "name": self.engine.name,
                       "can_learn": self.engine.can_learn,
                       "can_see": getattr(self.engine, "can_see", False)},
            "genome": {k: v for k, v in life.genome.to_dict().items() if k != "seed"},
            "needs": being.needs.to_dict(),
            "values": list(life.values),
            "milestones": dict(life.milestones),
            "questions": list(founding_questions(life.language)),
            "thoughts": life.state.get("thoughts", 0),
            "dialogue": list(being.dialogue),
            "memory_map": life.memory.map(),
            "dreams": len(life.dreams.ids()),
            "library": [life.library.public(item) for item in life.library.items()],
            "weights": dict(being.subconscious.weights),
            "affect": being.affect.summary(),
            "research": being.research.changed(),
            "inbox": len(being.inbox),
            "tempo": self.tempo,
            "thoughts_per_hour": self.thoughts_per_hour,
            "paused": self.paused_reason,
            "kernel": being.guard.fingerprint[:12],
            "seq": self._seq,
        }
        with self._changed:
            snapshot.update(activity=self._activity, sleeping=self._activity == "sleeping")
            self.snapshot = snapshot
            self._changed.notify_all()
