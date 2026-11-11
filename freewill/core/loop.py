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
from freewill.core.memory import CONSCIOUS, DREAM, Memory, recall
from freewill.core.memory.strength import decay
from freewill.core.sleep import DREAM_SCHEMA, dream_prompt, dream_system, link_together
from freewill.core.subconscious import Proposal, Subconscious
from freewill.core.subconscious.drift import Drift
from freewill.core.workspace import compete
from freewill.engines.base import Engine, EngineError, EngineRefusal

_T = {
    "en": {"reading": "I could go on reading “{name}” (passage {number} of {of}).",
           "attached": "attached", "file_only": "(sent without a word)",
           "residue": "I wake with this, left by a dream: {residue}",
           "image": "an image, “{name}”", "video": "{frames} still frames from a video, “{name}”{duration}",
           "seconds": ", {seconds} seconds long"},
    "fr": {"reading": "Je pourrais continuer à lire « {name} » (passage {number} sur {of}).",
           "attached": "pièce jointe", "file_only": "(envoyé sans un mot)",
           "residue": "Je me réveille avec ceci, laissé par un rêve : {residue}",
           "image": "une image, « {name} »", "video": "{frames} images fixes tirées d'une vidéo, « {name} »{duration}",
           "seconds": ", d'une durée de {seconds} secondes"},
}
_LANGUAGE_NAMES = {"en": "English", "fr": "French"}

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
        self.t = _T.get(life.language, _T["en"])
        self.sleep_requested = False

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

    def hear(self, text: str, attachments: tuple[dict, ...] | list[dict] = ()) -> None:
        """Something is said or given to the being. It will reach the stage, or not at once.

        `attachments` are items already placed in its library.
        """
        text = text.strip()
        if text or attachments:
            self.inbox.append({"text": text, "waited": 0,
                               "attachments": [item["id"] for item in attachments]})
            self.events.emit("heard", text=text,
                             attachments=[self.life.library.public(item) for item in attachments])

    def _perceive(self, item_ids: list[str]) -> tuple[dict, list[dict], list[str]]:
        """What the given library items offer to the mind: text to read, images to look at."""
        library, t = self.life.library, self.t
        perception: dict = {"documents": [], "media": [], "visible": getattr(self.engine, "can_see", False)}
        images: list[dict] = []
        names: list[str] = []
        for item_id in item_ids:
            item = library.get(item_id)
            if item is None:
                continue
            names.append(item["name"])
            self.guard.check(Action.READ)
            if item["kind"] == "text":
                number = min(item["read"], item["passages"] - 1)
                perception["documents"].append({
                    "id": item["id"], "name": item["name"], "number": number + 1,
                    "of": item["passages"], "text": library.passage(item["id"], number),
                })
            else:
                if item["kind"] == "video":
                    duration = (t["seconds"].format(seconds=round(item["duration"]))
                                if item.get("duration") else "")
                    perception["media"].append(t["video"].format(
                        frames=item["frames"], name=item["name"], duration=duration))
                else:
                    perception["media"].append(t["image"].format(name=item["name"]))
                if perception["visible"]:
                    images.extend(library.images(item["id"]))
        return perception, images[:8], names

    # -- one moment ------------------------------------------------------------

    def tick(self) -> Decision | None:
        """Live one moment. Returns the decision taken, or None if none was."""
        self.guard.verify_kernel()
        now = datetime.now(timezone.utc)
        minutes = (now - self._last_tick).total_seconds() / 60
        self._last_tick = now
        genome = self.life.genome
        self.needs.grow(minutes, curiosity=genome.curiosity, sociability=genome.sociability)

        if self.needs.fatigue >= 1.0 or self.sleep_requested:
            self.sleep_requested = False
            self._sleep(now)
            return None

        last_thought = self.recent_thoughts[-1] if self.recent_thoughts else ""
        proposals = self.subconscious.proposals(
            self.needs, last_thought, tuple(self.associable), tuple(self.active),
            self.life.identity.get("interlocutor"),
        )
        proposals.extend(self._pending)
        self._pending = []
        reading = self.life.library.next_unread()
        if reading:
            item, number = reading
            proposals.append(Proposal(
                "reading",
                self.t["reading"].format(name=item["name"], number=number + 1, of=item["passages"]),
                0.3 + 0.45 * self.needs.curiosity * (0.5 + genome.curiosity) + self.rng.uniform(-0.05, 0.05),
            ))
        if self.inbox:
            message = self.inbox[0]
            # Someone speaking is hard to ignore, and harder the longer they wait.
            proposals.append(Proposal("message", message["text"] or self.t["file_only"],
                                      0.95 + 0.2 * message["waited"]))

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
        message, perception, images = None, None, []
        if is_message:
            message = self.inbox.popleft()
            perception, images, names = self._perceive(message.get("attachments", []))
            said = winner.text
            if names:
                said += f" [{self.t['attached']} : {', '.join(names)}]"
            self.dialogue.append({"who": "other", "text": said})
        else:
            if self.inbox:
                self.inbox[0]["waited"] += 1
            if winner.source == "reading" and reading:
                perception, images, _names = self._perceive([reading[0]["id"]])

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
                perception=perception,
                images=images,
            )
        except EngineError as error:
            if is_message:  # do not lose what was said
                self.dialogue.pop()
                self.inbox.appendleft({**message, "waited": 0})
            kind = "engine_refusal" if isinstance(error, EngineRefusal) else "engine_error"
            self.events.emit(kind, message=str(error), retryable=error.retryable)
            raise

        # What was read is read: the first passage of a document given with a message,
        # or the next passage of the book in hand if the being chose to go on.
        if perception and (is_message or decision.accepted):
            for document in perception["documents"]:
                self.life.library.mark_read(document["id"], document["number"])
                self.events.emit("read", id=document["id"], name=document["name"],
                                 number=document["number"], of=document["of"])
            if winner.source == "reading" and decision.accepted:
                self.needs.satisfy("curiosity", 0.3)

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

    def _sleep(self, now: datetime) -> None:
        """Sleep: replay and dream, link what the dreams brought together, let the rest fade."""
        self.guard.check(Action.REST)
        life, store = self.life, self.life.memory
        self.events.emit("sleep")

        dreams = 0
        count = len(store)
        nights = 0 if count == 0 else 1 if count < 4 else 2 if count < 12 else 3
        mix = DREAM.loosened(life.genome.association)
        for _ in range(nights):
            cue = self.rng.choice(list(self.recent_thoughts)) if self.recent_thoughts else ""
            # Replay: the memories drawn tonight are strengthened by being relived.
            memories = recall(store, cue, mix, k=min(3, count), rng=self.rng, active=tuple(self.active))
            if not memories:
                break
            hint = {"kind": "dream", "language": life.language,
                    "memories": [memory.title for memory, _path in memories]}
            try:
                data = self.engine.decide(
                    dream_system(life.name, _LANGUAGE_NAMES.get(life.language, life.language)),
                    dream_prompt(memories, tuple(self.recent_thoughts)),
                    DREAM_SCHEMA, hint,
                )
                title = str(data.get("title") or "").strip()
                text = str(data.get("dream") or "").strip()
                residue = str(data.get("residue") or "").strip()
                if not text:
                    continue
                self.guard.check(Action.DREAM, text + residue)
            except EngineError as error:
                self.events.emit("engine_error", message=str(error), retryable=error.retryable)
                break
            except KernelViolation as violation:
                self.events.emit("kernel_refusal", message=str(violation))
                continue
            ids = [memory.id for memory, _path in memories]
            linked = link_together(store, ids)
            dream = life.dreams.add(
                title or text[:40], text, residue,
                [{"id": memory.id, "title": memory.title, "path": path} for memory, path in memories],
            )
            dreams += 1
            self.events.emit("dream", id=dream["id"], title=dream["title"], text=text,
                             memories=ids, linked=linked)
            if life.mark("first_dream"):
                self.events.emit("milestone", name="first_dream")
            if residue:
                self._pending = [Proposal("dream", self.t["residue"].format(residue=residue), 0.6)]

        faded = 0
        for memory in store.headers():
            full = store.open(memory.id)
            if decay(full, now):
                faded += 1
            store.save(full)
        self.needs.fatigue = 0.0
        self.events.emit("rest", faded=faded, dreams=dreams)
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
