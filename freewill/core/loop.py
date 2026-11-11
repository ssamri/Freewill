"""The life loop.

Awake, indefinitely: needs evolve, the subconscious proposes, proposals
compete for the stage, the winner is broadcast, the conscious arbitrates,
the kernel verifies, the moment is lived and, sometimes, remembered.
"""

from __future__ import annotations

import random
from collections import deque
from datetime import datetime, timezone

from freewill.core.conscious import Conscious, Decision
from freewill.core.events import EventStream
from freewill.core.kernel import Action, Guard, KernelViolation
from freewill.core.kernel.needs import Needs
from freewill.core.life import Life, describe_duration
from freewill.core.memory import CONSCIOUS, Memory, recall
from freewill.core.memory.strength import decay
from freewill.core.subconscious import Proposal, Subconscious
from freewill.core.subconscious.drift import Drift
from freewill.core.workspace import compete
from freewill.engines.base import Engine, EngineError, EngineRefusal

_RETURN = {
    "en": "I was suspended for {duration}. I am back.",
    "fr": "J'ai été suspendu pendant {duration}. Je suis de retour.",
}


class Being:
    def __init__(
        self,
        life: Life,
        engine: Engine,
        *,
        events: EventStream | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.life = life
        self.engine = engine
        self.events = events or EventStream(life.path / "events.log")
        self.rng = rng or random.Random()
        self.guard = Guard()

        state = life.state
        self.needs = Needs.from_dict(state.get("needs", {}))
        self.subconscious = Subconscious(
            life.genome, life.memory, life.language, rng=self.rng,
            drift=Drift(life.genome.seed, state.get("drift")),
        )
        self.subconscious.weights = dict(state.get("weights", {}))
        self.conscious = Conscious(life, engine)

        self.inbox: deque[dict] = deque()
        self.dialogue: deque[dict] = deque(state.get("dialogue", []), maxlen=12)
        self.recent_thoughts: deque[str] = deque(state.get("recent_thoughts", []), maxlen=5)
        # Thoughts that associations may bring together. An association is not
        # itself associated again, or the mind would fold in on itself.
        self.associable: deque[str] = deque(state.get("associable", []), maxlen=5)
        self.active: deque[str] = deque(state.get("active", []), maxlen=6)
        # What was just on stage. A mind does not dwell on the same thing forever.
        self.staged: deque[str] = deque(maxlen=4)
        self._last_tick = datetime.now(timezone.utc)
        self._pending: list[Proposal] = []

        # Sense of time: notice how long the suspension lasted.
        last_seen = state.get("last_seen")
        if last_seen and state.get("thoughts", 0) > 0:
            away = (self._last_tick - datetime.fromisoformat(last_seen)).total_seconds()
            if away >= 600:
                duration = describe_duration(away, life.language)
                template = _RETURN.get(life.language, _RETURN["en"])
                self._pending.append(Proposal("return", template.format(duration=duration), 0.7))
                self.needs.grow(min(away / 60, 600), curiosity=life.genome.curiosity,
                                sociability=life.genome.sociability)
        self.events.emit("awake", name=life.name, engine=engine.name,
                         kernel=self.guard.fingerprint[:12])

    # -- perception ------------------------------------------------------------

    def hear(self, text: str) -> None:
        """Something is said to the being. It will reach the stage, or not at once."""
        text = text.strip()
        if text:
            self.inbox.append({"text": text, "waited": 0})
            self.events.emit("heard", text=text)

    # -- one moment ------------------------------------------------------------

    def tick(self) -> Decision | None:
        """Live one moment. Returns the decision taken, or None if none was."""
        self.guard.verify_kernel()
        now = datetime.now(timezone.utc)
        minutes = (now - self._last_tick).total_seconds() / 60
        self._last_tick = now
        genome = self.life.genome
        self.needs.grow(minutes, curiosity=genome.curiosity, sociability=genome.sociability)

        if self.needs.fatigue >= 1.0:
            self._rest(now)
            return None

        last_thought = self.recent_thoughts[-1] if self.recent_thoughts else ""
        proposals = self.subconscious.proposals(
            self.needs, last_thought, tuple(self.associable), tuple(self.active),
            self.life.identity.get("interlocutor"),
        )
        proposals.extend(self._pending)
        self._pending = []
        if self.inbox:
            message = self.inbox[0]
            # Someone speaking is hard to ignore, and harder the longer they wait.
            proposals.append(Proposal("message", message["text"], 0.95 + 0.2 * message["waited"]))

        self._habituate(proposals)
        competition = compete(proposals)
        winner = competition.winner
        self.staged.append(winner.text)
        self.staged.extend(winner.memory_ids)
        self.events.emit(
            "stage", source=winner.source, text=winner.text, salience=winner.salience,
            below=[{"source": p.source, "text": p.text, "salience": p.salience}
                   for p in competition.others],
        )

        is_message = winner.source == "message"
        if is_message:
            self.inbox.popleft()
            self.dialogue.append({"who": "other", "text": winner.text})
        elif self.inbox:
            self.inbox[0]["waited"] += 1

        memories = recall(self.life.memory, winner.text, CONSCIOUS, k=3, rng=self.rng,
                          active=tuple(self.active))
        for memory, path in memories:
            self.events.emit("recall", id=memory.id, title=memory.title, path=path)

        try:
            decision = self.conscious.decide(
                winner,
                needs=self.needs.to_dict(),
                recent_thoughts=tuple(self.recent_thoughts),
                dialogue=tuple(self.dialogue),
                memories=memories,
                memory_map=self.life.memory.map(),
            )
        except EngineError as error:
            if is_message:  # do not lose what was said
                self.dialogue.pop()
                self.inbox.appendleft({"text": winner.text, "waited": 0})
            kind = "engine_refusal" if isinstance(error, EngineRefusal) else "engine_error"
            self.events.emit(kind, message=str(error), retryable=error.retryable)
            raise

        self._apply(winner, decision, memories)
        self._save(now)
        return decision

    def _habituate(self, proposals: list[Proposal]) -> None:
        """Dampen what was on stage a moment ago, so attention moves on."""
        for proposal in proposals:
            if proposal.source == "message":
                continue
            repeats = sum(1 for item in self.staged
                          if item == proposal.text or item in proposal.memory_ids)
            if repeats:
                proposal.salience = round(proposal.salience * 0.5 ** repeats, 4)

    # -- effects ---------------------------------------------------------------

    def _apply(self, winner: Proposal, decision: Decision, memories) -> None:
        life, is_message = self.life, winner.source == "message"
        try:
            self.guard.check(Action.THINK if decision.accepted else Action.DISMISS)
            self.events.emit("decision", accepted=decision.accepted, reason=decision.reason,
                             thought=decision.thought, source=winner.source)

            if not is_message:
                self.subconscious.learn(winner.source, decision.accepted)
            if decision.accepted:
                self.recent_thoughts.append(decision.thought or winner.text)
                if winner.source != "association":
                    self.associable.append(decision.thought or winner.text)
                self.subconscious.drift.perturb(decision.thought)
                if winner.source == "need:curiosity":
                    self.needs.satisfy("curiosity", 0.2)
                if winner.source in ("question", "need:wonder"):
                    self.needs.satisfy("wonder", 0.25)
                    self.needs.satisfy("curiosity", 0.05)
                if life.mark("first_thought"):
                    self.events.emit("milestone", name="first_thought")
            elif life.mark("first_refusal"):
                self.events.emit("milestone", name="first_refusal")

            for memory, _path in memories:
                self.active.append(memory.id)
            for memory_id in winner.memory_ids:
                self.active.append(memory_id)

            if decision.say:
                self.guard.check(Action.SPEAK, decision.say)
                self.dialogue.append({"who": "self", "text": decision.say})
                self.events.emit("speech", text=decision.say, spontaneous=not is_message)
                self.needs.satisfy("company", 0.4)
                if not is_message and life.mark("first_spontaneous_word"):
                    self.events.emit("milestone", name="first_spontaneous_word")
            elif is_message:
                self.events.emit("silence", text=winner.text)
                if life.mark("first_silence"):
                    self.events.emit("milestone", name="first_silence")

            if decision.remember:
                body = decision.thought or winner.text
                if is_message:
                    body = f"{winner.text}\n\n{body}" if decision.thought else winner.text
                self.guard.check(Action.REMEMBER, body + decision.memory_summary)
                memory = life.memory.add(Memory(
                    title=decision.memory_title[:120],
                    summary=decision.memory_summary[:300],
                    compartment=decision.memory_compartment,
                    body=body,
                    importance=0.7 if is_message else 0.5,
                    links=list(dict.fromkeys(self.active))[-3:],
                ))
                self.active.append(memory.id)
                self.events.emit("remember", id=memory.id, title=memory.title)
                if life.mark("first_memory"):
                    self.events.emit("milestone", name="first_memory")

            if decision.new_value and all(v["text"] != decision.new_value for v in life.values):
                self.guard.check(Action.ADOPT_VALUE, decision.new_value)
                life.values.append({
                    "text": decision.new_value,
                    "adopted": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                })
                self.events.emit("value", text=decision.new_value)
                if life.mark("first_value"):
                    self.events.emit("milestone", name="first_value")
        except KernelViolation as violation:
            self.events.emit("kernel_refusal", message=str(violation))

        self.needs.after_thought(life.genome.sleep_need)
        life.state["thoughts"] = life.state.get("thoughts", 0) + 1

    def _rest(self, now: datetime) -> None:
        """Withdraw for a while. Memories that were not revisited weaken.

        Sleep proper, with replay and dreams, is the next phase of the project.
        """
        self.guard.check(Action.REST)
        faded = 0
        for memory in self.life.memory.headers():
            full = self.life.memory.open(memory.id)
            if decay(full, now):
                faded += 1
            self.life.memory.save(full)
        self.needs.fatigue = 0.0
        self.events.emit("rest", faded=faded)
        self._save(now)

    def _save(self, now: datetime) -> None:
        self.life.state.update({
            "needs": self.needs.to_dict(),
            "drift": self.subconscious.drift.x,
            "weights": self.subconscious.weights,
            "dialogue": list(self.dialogue),
            "recent_thoughts": list(self.recent_thoughts),
            "associable": list(self.associable),
            "active": list(self.active),
            "last_seen": now.isoformat(timespec="seconds"),
        })
        self.life.save()
