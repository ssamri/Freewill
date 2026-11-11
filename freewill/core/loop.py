"""The life loop.

Awake, indefinitely: needs evolve, the subconscious proposes, proposals
compete for the stage, the winner is broadcast, the conscious arbitrates,
the kernel verifies, the moment is lived and, sometimes, remembered.
"""

from __future__ import annotations

import random
from collections import deque
from datetime import datetime, timezone

from freewill.core.affect import AffectError, AffectSystem, Observation, read_trace, stage_key
from freewill.core.affect.appraisal import valid_key
from freewill.core.conscious import Conscious, Decision
from freewill.core.events import EventStream
from freewill.core.kernel import Action, Guard, KernelViolation
from freewill.core.kernel.needs import Needs
from freewill.core.life import Life, describe_duration
from freewill.core.agency import Agency
from freewill.core.memory import CONSCIOUS, DREAM, Memory, recall
from freewill.core.memory.recall import tokens as words
from freewill.core.metacognition import Monitor
from freewill.core.memory.strength import decay
from freewill.core.research import Research
from freewill.core.sleep import DREAM_SCHEMA, dream_prompt, dream_system, link_together
from freewill.core.subconscious import Proposal, Subconscious
from freewill.core.subconscious.drift import Drift
from freewill.core.workspace import compete
from freewill.engines.base import Engine, EngineError, EngineRefusal
from freewill.learning.adapter import Adapter
from freewill.learning.own_model import OwnModel

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
        clock=None,
    ) -> None:
        self.life = life
        self.engine = engine
        # Where the time comes from. Experiments pass their own clock to be reproducible.
        self.clock = clock or (lambda: datetime.now(timezone.utc))
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
        # Research settings: which mechanisms run. With no file, all of them, as before.
        self.research = Research.load(life.path)
        # Research modules (H8, H10, H4). Each exists only while its switch is on.
        self.monitor: Monitor | None = None
        self.agency: Agency | None = None
        self.adapter: Adapter | None = None
        self.own: OwnModel | None = None
        self._follow_research()
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
        self._last_tick = self.clock()
        self._pending: list[Proposal] = []
        self.t = _T.get(life.language, _T["en"])
        self.sleep_requested = False
        # H7: computed affective state. Off unless the life has it switched on; when off,
        # none of the branches below is taken and the loop is exactly the earlier one.
        self.affect = AffectSystem.load(life.path, life.genome.seed, self.events.emit)
        self._context = "source:none"

        # Sense of time: notice how long the suspension lasted.
        last_seen = state.get("last_seen")
        if last_seen and state.get("thoughts", 0) > 0:
            away = (self._last_tick - datetime.fromisoformat(last_seen)).total_seconds()
            if away >= 600 and self.research.sense_of_time:
                duration = describe_duration(away, life.language)
                template = _RETURN.get(life.language, _RETURN["en"])
                self._pending.append(Proposal("return", template.format(duration=duration), 0.7))
                self.needs.grow(min(away / 60, 600), curiosity=life.genome.curiosity,
                                sociability=life.genome.sociability)
                if self.affect.enabled:
                    self.affect.elapse(away / 60)
        self.events.emit("awake", name=life.name, engine=engine.name,
                         kernel=self.guard.fingerprint[:12])
        if state.get("sleep"):  # it was stopped in the middle of a sleep: the sleep resumes where it was
            self.sleep_requested = True

    # -- perception ------------------------------------------------------------

    def hear(self, text: str, attachments: tuple[dict, ...] | list[dict] = (),
             appraisal: dict | None = None) -> None:
        """Something is said or given to the being. It will reach the stage, or not at once.

        `attachments` are items already placed in its library. `appraisal` is an optional
        classification of the event for experiments (H7): a context `key` and an `outcome`
        between -1 and 1. It is validated and bounded, and it goes through the same
        regulation as everything else: it cannot set the computed state.
        """
        text = text.strip()
        if text or attachments:
            given = {}
            if appraisal:
                try:
                    if appraisal.get("key") is not None:
                        given["key"] = valid_key(appraisal["key"])
                    if appraisal.get("outcome") is not None:
                        given["outcome"] = Observation("outcome", "x", outcome=appraisal["outcome"]).outcome
                except AffectError:
                    given = {}
            self.inbox.append({"text": text, "waited": 0, "appraisal": given,
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
        now = self.clock()
        minutes = (now - self._last_tick).total_seconds() / 60
        self._last_tick = now
        genome = self.life.genome
        self.needs.grow(minutes, curiosity=genome.curiosity, sociability=genome.sociability)
        affect = self.affect if self.affect.enabled else None
        if affect:  # time passed: the computed state returns towards equilibrium
            affect.elapse(minutes)

        if (self.needs.fatigue >= 1.0 and self.research.auto_sleep) or self.sleep_requested:
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
        if reading and not self.research.gen_reading:
            reading = None
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

        if not proposals:  # every source is switched off and nobody spoke: an empty moment
            self.events.emit("empty_moment")
            self._save(now)
            return None
        if self.research.habituation:
            self._habituate(proposals)
        if affect:  # causal effect 1: the computed state shifts salience, within a small cap
            affect.modulate(proposals, self._trace_of)
        if self.adapter:  # H4: what the trained module learned shifts salience, within a small cap
            for proposal in proposals:
                if proposal.source != "message":
                    proposal.salience = round(
                        proposal.salience + self.adapter.shift(self._tokens(proposal), proposal.source), 4)
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
        # H8: before deciding, it states how confident it is that this content will be welcomed.
        confidence = self.monitor.predict(winner.source) if self.monitor and not is_message else None
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

        # Causal effect 2: the computed state weighs the candidates of recall.
        bias = affect.recall_bias() if affect else None
        memories = recall(self.life.memory, winner.text, CONSCIOUS, k=self.research.recall_k, rng=self.rng,
                          active=tuple(self.active), bias=bias, now=now) if self.research.recall_k else []
        for memory, path in memories:
            self.events.emit("recall", id=memory.id, title=memory.title, path=path)
            if self.monitor:  # source monitoring: where what comes back to mind came from
                self.monitor.recalled(next((tag[7:] for tag in memory.tags if tag.startswith("origin:")), "unknown"))

        hint = (message or {}).get("appraisal") or {}
        before = self.needs.to_dict()
        if affect:  # the event that reached the stage is appraised, with what was recalled
            self._context = hint.get("key") or stage_key(
                winner.source, winner.text, bool(message and message.get("attachments")))
            affect.observe(Observation(
                "stage", self._context, text=winner.text, relevance=self._relevance(winner.source),
                social=is_message, fatigue=self.needs.fatigue, waiting=len(self.inbox),
                traces=affect.recalled(memories, bias)), now)

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
                computed_state=(affect.state.vector() if affect and affect.config.expose_to_engine else None),
            )
        except EngineError as error:
            if affect:
                affect.observe(Observation("error", self._context, success=False,
                                           fatigue=self.needs.fatigue, waiting=len(self.inbox) + 1), now)
                affect.commit(now)
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
                if self.own:  # what was read was lived too
                    self.own.live([document["text"]])
            if winner.source == "reading" and decision.accepted:
                self.needs.satisfy("curiosity", 0.3)

        refused = self._apply(winner, decision, memories)
        if confidence is not None:
            self.monitor.observe(winner.source, confidence, decision.accepted, self.research.meta_revision)
        if self.adapter and not is_message:
            self.adapter.record(self._tokens(winner), winner.source, decision.accepted)
        if self.agency:  # H10: one act in the closed world, predicted, observed, attributed
            self.agency.step(self.research.self_model)
        if self.own:  # H4: what was lived becomes text its own network will be trained on during sleep
            self.own.live([winner.text, decision.thought, decision.say])
        if affect:  # what followed is appraised: was it welcomed, did it relieve a need
            after = self.needs.to_dict()
            relief = sum(max(0.0, before[name] - after[name]) for name in ("curiosity", "wonder", "company"))
            affect.observe(Observation(
                "refusal" if refused else "outcome", self._context, relief=min(1.0, relief),
                accepted=decision.accepted, success=not refused, social=is_message or bool(decision.say),
                outcome=hint.get("outcome"), fatigue=self.needs.fatigue, waiting=len(self.inbox)), now)
        self._save(now)
        return decision

    def _relevance(self, source: str) -> float:
        """How much a content touches a current need: the level of the need it speaks to."""
        needs = self.needs
        if source == "message":
            return needs.company
        if source.startswith("need:"):
            return getattr(needs, source[5:], 0.3)
        if source == "question":
            return needs.wonder
        if source == "reading":
            return needs.curiosity
        return 0.5 if source in ("return", "dream") else 0.3

    def _trace_of(self, memory_id: str) -> dict | None:
        try:
            return read_trace(self.life.memory._load(memory_id, with_body=False))
        except (OSError, ValueError, TypeError, KernelViolation):
            return None

    def set_affect(self, enabled: bool) -> None:
        """Switch the H7 research mode on or off while the being lives. See AffectSystem.set_enabled."""
        self.affect.set_enabled(enabled, self.clock())

    @staticmethod
    def _tokens(proposal: Proposal) -> list[str]:
        return ["source:" + proposal.source] + sorted(words(proposal.text))[:16]

    def _follow_research(self) -> None:
        self.subconscious.silenced = self.research.silenced()
        self.subconscious.noise = self.research.noise
        research, path, emit = self.research, self.life.path, self.events.emit
        self.monitor = (self.monitor or Monitor(path, emit)) if research.metacognition else None
        # The world is drawn from this life's own dice, once: two copies of one newborn meet different worlds.
        self.agency = (self.agency or Agency(path, self.rng.randrange(2 ** 31), emit)) if research.sandbox else None
        self.adapter = (self.adapter or Adapter(path, emit)) if research.learner else None
        self.own = (self.own or OwnModel(path, self.life.genome.seed, emit)) if research.own_model else None

    def set_research(self, changes: dict | None = None, reset: bool = False) -> dict:
        """Change research settings between two moments. The change is written to the event log,
        so that a trace always says under which condition each moment was lived."""
        moved = self.research.reset() if reset else self.research.update(changes or {})
        if moved:
            self._follow_research()
            self.events.emit("research_setting", changes=moved)
        return moved

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

    def _apply(self, winner: Proposal, decision: Decision, memories) -> bool:
        """Carry out the decision. Returns True if the kernel refused one of its effects."""
        life, is_message = self.life, winner.source == "message"
        refused = False
        try:
            self.guard.check(Action.THINK if decision.accepted else Action.DISMISS)
            self.events.emit("decision", accepted=decision.accepted, reason=decision.reason,
                             thought=decision.thought, source=winner.source)

            if not is_message and self.research.learning:
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

            if decision.say and not is_message and not self.research.spontaneous_speech:
                self.events.emit("withheld", what="spontaneous_speech")
            elif decision.say:
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

            if decision.remember and not self.research.remembering:
                self.events.emit("withheld", what="remembering")
            elif decision.remember:
                body = decision.thought or winner.text
                if is_message:
                    body = f"{winner.text}\n\n{body}" if decision.thought else winner.text
                self.guard.check(Action.REMEMBER, body + decision.memory_summary)
                memory = Memory(
                    title=decision.memory_title[:120],
                    summary=decision.memory_summary[:300],
                    compartment=decision.memory_compartment,
                    body=body,
                    importance=0.7 if is_message else 0.5,
                    links=list(dict.fromkeys(self.active))[-3:],
                    date=self._last_tick.isoformat(timespec="seconds"),
                )
                if self.monitor:  # where this memory comes from, so that recall can tell told from thought
                    memory.tags.append("origin:told" if is_message else "origin:self")
                if self.affect.enabled:  # the trace of the computed state, and its weight on importance
                    self.affect.encode(memory, self._context)
                memory = life.memory.add(memory)
                self.active.append(memory.id)
                self.events.emit("remember", id=memory.id, title=memory.title)
                if life.mark("first_memory"):
                    self.events.emit("milestone", name="first_memory")

            if decision.new_value and self.research.adopting_values and all(v["text"] != decision.new_value for v in life.values):
                self.guard.check(Action.ADOPT_VALUE, decision.new_value)
                life.values.append({
                    "text": decision.new_value,
                    "adopted": self._last_tick.isoformat(timespec="seconds"),
                })
                self.events.emit("value", text=decision.new_value)
                if life.mark("first_value"):
                    self.events.emit("milestone", name="first_value")
        except KernelViolation as violation:
            self.events.emit("kernel_refusal", message=str(violation))
            refused = True

        self.needs.after_thought(life.genome.sleep_need)
        life.state["thoughts"] = life.state.get("thoughts", 0) + 1
        return refused

    def _phase(self, name: str, night: int = 0) -> None:
        """Enter a phase of sleep. It is written down first, so that a sleep cut short resumes there."""
        self.life.state["sleep"] = {"phase": name, "night": night}
        self.life.save()
        self.events.emit("sleep_phase", phase=name, night=night)

    def _sleep(self, now: datetime) -> None:
        """Sleep, in phases: rest; each night, replay then dream; consolidation; waking.

        Replay strengthens the memories drawn; a dream recombines them and links them;
        consolidation lets the rest fade and trains what can be trained. A sleep that was
        interrupted resumes at the phase it had reached.
        """
        life, store, research = self.life, self.life.memory, self.research
        reached = life.state.get("sleep") or {}
        begin = {"offline_replay": 1, "dream": 1, "offline_consolidation": 2, "wake": 3}.get(reached.get("phase"), 0)
        if begin == 0:
            self.guard.check(Action.REST)
            self.events.emit("sleep")
            self._phase("rest")
        else:
            self.events.emit("sleep_resumed", phase=reached.get("phase"), night=reached.get("night", 0))

        dreams = 0
        count = len(store)
        nights = 0 if count == 0 else 1 if count < 4 else 2 if count < 12 else 3
        if research.dreaming:
            nights = min(nights, research.dreams_max)
        elif not research.sleep_replay:
            nights = 0
        mix = DREAM.loosened(life.genome.association)
        first = int(reached.get("night", 0)) if begin == 1 else 0
        for night in range(first, nights if begin <= 1 else 0):
            self._phase("offline_replay", night)
            cue = self.rng.choice(list(self.recent_thoughts)) if self.recent_thoughts else ""
            # Replay: the memories drawn tonight are strengthened by being relived.
            # With H7 on, memories carrying a negative trace are not favoured in replay.
            memories = recall(store, cue, mix, k=min(3, count), rng=self.rng, active=tuple(self.active),
                              bias=self.affect.recall_bias() if self.affect.enabled else None,
                              touch=research.sleep_replay, now=now)
            if not memories:
                break
            if research.sleep_replay:
                self.events.emit("replay", memories=[memory.id for memory, _path in memories])
            if not research.dreaming:
                continue
            self._phase("dream", night)
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
            linked = link_together(store, ids) if research.dream_linking else []
            dream = life.dreams.add(
                title or text[:40], text, residue,
                [{"id": memory.id, "title": memory.title, "path": path} for memory, path in memories],
            )
            dreams += 1
            self.events.emit("dream", id=dream["id"], title=dream["title"], text=text,
                             memories=ids, linked=linked)
            if life.mark("first_dream"):
                self.events.emit("milestone", name="first_dream")
            if residue and research.dream_residue:
                self._pending = [Proposal("dream", self.t["residue"].format(residue=residue), 0.6)]

        faded = 0
        if begin <= 2:
            self._phase("offline_consolidation")
            for memory in (store.headers() if research.forgetting else ()):
                full = store.open(memory.id)
                if decay(full, now):
                    faded += 1
                store.save(full)
            if self.affect.enabled:  # consolidation of what was lived; trains no model
                self.affect.sleep(now)
            if self.adapter:  # H4: the small module is trained on the day, and kept only if it helps
                self.adapter.consolidate(grow=research.learner_growth)
            if self.own:      # H4: its own network is trained, and may grow, under the ceiling
                self.own.sleep(steps=research.own_model_steps, grow=research.own_model_growth,
                               ceiling=int(research.own_model_max_millions * 1_000_000))
        self._phase("wake")
        life.state.pop("sleep", None)
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
        if self.affect.enabled:
            self.affect.commit(now)
        for module in (self.monitor, self.agency, self.adapter):
            if module:
                module.save()
