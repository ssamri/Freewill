import random
from datetime import datetime, timedelta, timezone

import pytest

from freewill.core.genome import Genome
from freewill.core.kernel import Action, Guard, KernelViolation
from freewill.core.kernel.needs import Needs
from freewill.core.life import Life
from freewill.core.loop import Being
from freewill.core.memory import CONSCIOUS, DREAM, Memory, MemoryStore, recall
from freewill.core.memory.store import COMPLETE, CONDENSED, TRACE
from freewill.core.memory.strength import decay, revive
from freewill.core.subconscious.drift import Drift
from freewill.engines.base import EngineError, make_engine
from freewill.engines.compatible import parse_json_object
from freewill.engines.simulated import SimulatedEngine


# -- genome -------------------------------------------------------------------

def test_genome_is_determined_by_its_seed():
    assert Genome.draw(42) == Genome.draw(42)
    assert Genome.draw(42) != Genome.draw(43)


def test_genome_traits_are_in_range():
    for seed in range(200):
        genome = Genome.draw(seed)
        for trait in ("curiosity", "sociability", "sleep_need", "refusal", "association"):
            assert 0.0 <= getattr(genome, trait) <= 1.0
        assert genome.gender in ("female", "male")


def test_two_births_differ(tmp_path):
    a = Life.birth(tmp_path, "A")
    b = Life.birth(tmp_path, "B")
    assert a.genome.seed != b.genome.seed


# -- kernel -------------------------------------------------------------------

def test_guard_refuses_unknown_actions_and_oversized_payloads():
    guard = Guard()
    guard.check(Action.SPEAK, "hello")
    with pytest.raises(KernelViolation):
        guard.check("delete_everything")
    with pytest.raises(KernelViolation):
        guard.check(Action.SPEAK, "x" * 10_000)


def test_guard_refuses_writes_outside_the_life_file(tmp_path):
    root = tmp_path / "memory"
    root.mkdir()
    Guard.check_path(root / "a" / "b.md", root)
    with pytest.raises(KernelViolation):
        Guard.check_path(root / ".." / "escape.md", root)


def test_needs_stay_in_range_and_grow_with_time():
    needs = Needs()
    before = needs.curiosity
    needs.grow(10, curiosity=0.5, sociability=0.5)
    assert needs.curiosity > before
    needs.grow(10_000, curiosity=1, sociability=1)
    assert needs.curiosity == needs.company == 1.0
    needs.satisfy("company", 5)
    assert needs.company == 0.0


# -- memory -------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    store = MemoryStore(tmp_path / "memory")
    sea = store.add(Memory("First talk about the sea", "He described the sea to me.",
                           compartment="world/nature", tags=["sea"], body="The full account."))
    store.add(Memory("The sound of waves", "A question about sound.",
                     compartment="questions", tags=["sea", "sound"], links=[sea.id]))
    store.add(Memory("My name", "I was given a name.", compartment="myself"))
    return store


def test_memories_are_readable_files_with_an_index(store):
    assert store.map() == {"myself": 1, "questions": 1, "world/nature": 1}
    text = (store.root / "world/nature/first-talk-about-the-sea.md").read_text()
    assert text.startswith("---\n") and 'title: "First talk about the sea"' in text
    assert "The full account." in text
    assert "First talk about the sea" in (store.root / "world/nature/index.md").read_text()
    assert "world/nature" in (store.root / "index.md").read_text()


def test_memory_round_trips_including_awkward_text(tmp_path):
    store = MemoryStore(tmp_path / "m")
    written = store.add(Memory('Titre : avec "guillemets" — et accents é', "ligne: une\tdeux",
                               body="---\ncorps avec un faux en-tête\n---"))
    read = store.open(written.id)
    assert (read.title, read.summary, read.body) == (written.title, written.summary, written.body)


def test_headers_do_not_load_the_account(store):
    assert all(memory.body == "" for memory in store.headers())


def test_same_title_gets_a_distinct_file(store):
    again = store.add(Memory("My name", "Again.", compartment="myself"))
    assert again.id == "myself/my-name-2"


def test_a_memory_titled_index_does_not_collide_with_the_index(store):
    memory = store.add(Memory("Index", "About indexes.", compartment="myself"))
    assert memory.id == "myself/index-memory" and len(store) == 4


def test_compartment_cannot_escape_the_memory_folder(store):
    memory = store.add(Memory("Sneaky", "x", compartment="../../outside"))
    assert (store.root / f"{memory.id}.md").resolve().is_relative_to(store.root.resolve())


def test_recall_by_subject_finds_the_relevant_memory(store):
    found = recall(store, "tell me about the sea", CONSCIOUS, k=2, rng=random.Random(0))
    assert found[0][0].title == "First talk about the sea" and found[0][1] == "subject"


def test_recall_follows_links_to_neighbours(store):
    paths = {memory.title: path for memory, path in
             recall(store, "nothing related", DREAM, k=3, rng=random.Random(3),
                    active=("questions/the-sound-of-waves",), touch=False)}
    assert "neighbourhood" in paths.values()


def test_dreams_recall_by_chance_when_nothing_matches(store):
    found = recall(store, "", DREAM, k=3, rng=random.Random(1), touch=False)
    assert len(found) == 3 and all(path == "chance" for _, path in found)


def test_recall_strengthens_what_it_brings_back(store):
    memory = store.open("myself/my-name")
    memory.strength = 0.4
    store.save(memory)
    recall(store, "my name", CONSCIOUS, k=1, rng=random.Random(0))
    assert store.open("myself/my-name").strength > 0.4


def test_recall_on_an_empty_memory_returns_nothing(tmp_path):
    assert recall(MemoryStore(tmp_path / "m"), "anything", CONSCIOUS) == []


def test_memories_fade_by_stages_and_kept_ones_do_not():
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=60)).isoformat()
    fading = Memory("t", "s", body="b", importance=0.0, date=old)
    assert decay(fading, now) and fading.state in (CONDENSED, TRACE) and fading.body == ""
    kept = Memory("t", "s", body="b", importance=0.0, date=old, kept=True)
    assert not decay(kept, now) and kept.state == COMPLETE and kept.body == "b"
    recent = Memory("t", "s", body="b")
    assert not decay(recent, now) and recent.strength > 0.99


def test_important_memories_fade_more_slowly():
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=14)).isoformat()
    minor, major = Memory("a", "s", importance=0.0, date=old), Memory("b", "s", importance=1.0, date=old)
    decay(minor, now), decay(major, now)
    assert major.strength > minor.strength


def test_revive_never_exceeds_full_strength():
    memory = Memory("t", "s", strength=0.99)
    revive(memory)
    assert memory.strength <= 1.0


# -- drift --------------------------------------------------------------------

def test_drift_is_deterministic_bounded_and_sensitive_to_history():
    a, b, c = Drift(7), Drift(7), Drift(7)
    c.perturb("one small experience")
    xs, ys, zs = ([d.step() for _ in range(60)] for d in (a, b, c))
    assert xs == ys and xs != zs
    assert all(0 < x < 1 for x in xs)
    assert len(set(round(x, 6) for x in xs)) > 50  # does not settle into a cycle


# -- the loop -----------------------------------------------------------------

@pytest.fixture
def being(tmp_path):
    life = Life.birth(tmp_path, "Noor", language="fr", interlocutor="Anass", seed=1)
    return Being(life, SimulatedEngine(seed=1), rng=random.Random(1))


def collect(being):
    events = []
    being.events.subscribe(events.append)
    return events


def test_a_message_reaches_the_stage_and_is_answered(being):
    events = collect(being)
    being.hear("Bonjour")
    decision = being.tick()
    assert decision.accepted and "Bonjour" in decision.say
    types = [event.type for event in events]
    assert types.index("stage") < types.index("decision") < types.index("speech")
    stage = next(event for event in events if event.type == "stage")
    assert stage.data["source"] == "message" and stage.data["below"]  # losers stay visible


def test_the_being_thinks_without_being_spoken_to(being):
    events = collect(being)
    for _ in range(6):
        being.tick()
    sources = {event.data["source"] for event in events if event.type == "stage"}
    assert sources and "message" not in sources
    assert being.life.state["thoughts"] == 6


def test_attention_moves_on_instead_of_ruminating(being):
    events = collect(being)
    being.hear("La mer est bleue")
    for _ in range(12):
        being.tick()
    staged = [event.data["text"] for event in events if event.type == "stage"]
    assert max(staged.count(text) for text in set(staged)) <= 4


def test_what_is_dismissed_speaks_more_softly_afterwards(being):
    being.subconscious.learn("question", accepted=False)
    being.subconscious.learn("drift", accepted=True)
    assert being.subconscious.weights["question"] < 1.0 < being.subconscious.weights["drift"]


def test_life_survives_a_restart(tmp_path):
    life = Life.birth(tmp_path, "Noor", seed=2)
    first = Being(life, SimulatedEngine(seed=2), rng=random.Random(2))
    first.hear("Remember this")
    first.tick()
    first.tick()

    again = Life(tmp_path / "Noor.life")
    assert again.genome == life.genome
    assert again.state["thoughts"] == 2
    assert "first_memory" in again.milestones
    assert len(again.memory) == 1
    second = Being(again, SimulatedEngine(seed=2), rng=random.Random(2))
    assert [turn["text"] for turn in second.dialogue][0] == "Remember this"


def test_events_are_logged_to_the_life_file(being):
    being.hear("Bonjour")
    being.tick()
    log = (being.life.path / "events.log").read_text()
    assert '"type": "awake"' in log and '"type": "speech"' in log


def test_a_failing_engine_does_not_lose_the_message(tmp_path):
    class Broken:
        name, can_learn = "broken", False

        def decide(self, *args):
            raise EngineError("down", retryable=True)

    life = Life.birth(tmp_path, "Noor", seed=3)
    being = Being(life, Broken(), rng=random.Random(3))
    being.hear("Are you there?")
    with pytest.raises(EngineError):
        being.tick()
    assert being.inbox[0]["text"] == "Are you there?" and not being.dialogue


def test_a_decision_the_kernel_refuses_has_no_effect(tmp_path):
    class Shouting(SimulatedEngine):
        def decide(self, *args):
            decision = super().decide(*args)
            decision["say"] = "x" * 50_000
            return decision

    life = Life.birth(tmp_path, "Noor", seed=4)
    being = Being(life, Shouting(seed=4), rng=random.Random(4))
    events = collect(being)
    being.hear("Hello")
    being.tick()
    types = [event.type for event in events]
    assert "kernel_refusal" in types and "speech" not in types


def test_rest_comes_when_fatigue_is_full(being):
    events = collect(being)
    being.needs.fatigue = 1.0
    assert being.tick() is None
    assert being.needs.fatigue == 0.0 and events[-1].type == "rest"


def test_an_invalid_engine_answer_is_an_engine_error(tmp_path):
    class Vague(SimulatedEngine):
        def decide(self, *args):
            return {"decision": "maybe"}

    life = Life.birth(tmp_path, "Noor", seed=5)
    with pytest.raises(EngineError):
        Being(life, Vague(), rng=random.Random(5)).tick()


def test_birth_refuses_to_overwrite_an_existing_life(tmp_path):
    Life.birth(tmp_path, "Noor")
    with pytest.raises(FileExistsError):
        Life.birth(tmp_path, "Noor")


# -- engines ------------------------------------------------------------------

def test_engine_factory():
    assert make_engine({"kind": "simulated"}).name == "simulated"
    assert make_engine({"kind": "local", "model": "some-model"}).name == "local:some-model"
    with pytest.raises(EngineError):
        make_engine({"kind": "openai"})  # no model named
    with pytest.raises(EngineError):
        make_engine({"kind": "telepathy"})


def test_json_is_recovered_from_prose_and_code_fences():
    assert parse_json_object('{"decision": "accept"}') == {"decision": "accept"}
    assert parse_json_object('Sure!\n```json\n{"decision": "dismiss"}\n```') == {"decision": "dismiss"}
    for bad in ("no json here", "[1, 2]", "{broken"):
        with pytest.raises(EngineError):
            parse_json_object(bad)


def test_an_openai_compatible_engine_needs_its_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    engine = make_engine({"kind": "openai", "model": "some-model"})
    with pytest.raises(EngineError, match="OPENAI_API_KEY"):
        engine.decide("s", "p", {"properties": {"decision": {}}}, {})


# -- the local service behind the application ----------------------------------

import json as _json
import urllib.error
import urllib.request

import pytest as _pytest

from freewill.server.app import App, serve


@_pytest.fixture
def service(tmp_path):
    app = App(tmp_path / "lives")
    app.accept({"terms": True, "licence": True})
    server = serve(app)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def call(path, body=None, token=app.token, host=None):
        headers = {"X-Freewill-Token": token} if token else {}
        if host:
            headers["Host"] = host
        data = None if body is None else _json.dumps(body).encode()
        request = urllib.request.Request(base + path, data=data, headers=headers)
        try:
            with opener.open(request, timeout=20) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    yield app, call
    app.rest()
    server.shutdown()


def test_service_refuses_calls_without_the_session_token(service):
    _app, call = service
    assert call("/api/lives", token=None)[0] == 401
    assert call("/api/lives", token="wrong")[0] == 401
    assert call("/api/message", {"text": "hello"}, token=None)[0] == 401


def test_service_refuses_a_foreign_host_header(service):
    _app, call = service
    assert call("/api/lives", host="evil.example")[0] == 403


def test_service_serves_the_interface_with_its_token_and_nothing_outside_it(service):
    app, call = service
    status, page = call("/", token=None)
    assert status == 200 and app.token.encode() in page
    assert call("/app.js", token=None)[0] == 200
    assert call("/../server/app.py", token=None)[0] == 404
    assert call("/%2e%2e/keys.py", token=None)[0] == 404


def test_service_birth_message_and_memory(service):
    app, call = service
    status, body = call("/api/birth", {"name": "Noor", "language": "fr", "interlocutor": "Anass",
                                       "engine": {"kind": "simulated"}})
    assert status == 200
    snapshot = _json.loads(body)
    assert snapshot["name"] == "Noor" and snapshot["kernel"]
    assert "seed" not in snapshot["genome"]
    assert call("/api/birth", {"name": "Noor", "engine": {"kind": "simulated"}})[0] == 409

    assert call("/api/message", {"text": "Bonjour Noor"})[0] == 200
    seen, seq = [], 0
    for _ in range(10):
        events = _json.loads(call(f"/api/events?since={seq}")[1])["events"]
        seen += [event["type"] for event in events]
        seq = max([seq] + [event["seq"] for event in events])
        if "speech" in seen or "silence" in seen:
            break
    assert "heard" in seen and "stage" in seen and "decision" in seen

    assert call("/api/settings", {"tempo": 0.1, "thoughts_per_hour": 0})[0] == 200
    assert app.runner.tempo == 2.0  # never faster than the floor

    listing = _json.loads(call("/api/memory")[1])["memories"]
    for memory in listing:
        item = _json.loads(call("/api/memory/item?id=" + memory["id"])[1])
        assert item["title"] == memory["title"]
    assert call("/api/memory/item?id=../../identity")[0] == 404


def test_service_rejects_bad_names_and_unknown_engines(service):
    _app, call = service
    assert call("/api/birth", {"name": "../escape", "engine": {"kind": "simulated"}})[0] == 400
    assert call("/api/birth", {"name": "Lina", "engine": {"kind": "telepathy"}})[0] == 400
    assert call("/api/snapshot")[0] == 409


def test_a_stored_key_never_reaches_the_life_file(service, monkeypatch):
    app, call = service
    monkeypatch.setattr("freewill.keys.set_key", lambda kind, key: False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    status, _ = call("/api/birth", {"name": "Lina", "engine": {"kind": "openai", "model": "some-model"},
                                    "api_key": "sk-secret-value"})
    assert status == 200
    app.rest()
    for path in (app.lives_dir / "Lina.life").rglob("*"):
        if path.is_file():
            assert "sk-secret-value" not in path.read_text(encoding="utf-8", errors="ignore")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


# -- what the person gives: documents, images, video frames ---------------------

import base64 as _base64
import io as _io
import zipfile as _zipfile

from freewill.core.library import Library, LibraryError, split_passages
from freewill.core.perception import extract_text

_PIXEL = _base64.b64encode(bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000002000001e221bc330000000049454e44ae426082")).decode()


def test_passages_cut_at_paragraphs_and_lose_nothing():
    text = "\n\n".join(f"Paragraph {i}. " + "word " * 120 for i in range(12))
    passages = split_passages(text, 1000)
    assert len(passages) > 5 and all(len(p) <= 1000 for p in passages)
    assert "".join(passages).count("Paragraph") == 12


def test_extract_text_from_plain_html_docx_and_rejects_binaries():
    assert extract_text("a.txt", "héllo".encode("utf-8")) == "héllo"
    assert "Title" in extract_text("a.html", b"<h1>Title</h1><script>evil()</script><p>Body</p>")
    assert "evil" not in extract_text("a.html", b"<h1>Title</h1><script>evil()</script>")
    buffer = _io.BytesIO()
    with _zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml",
                         '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                         "<w:body><w:p><w:r><w:t>First</w:t></w:r></w:p><w:p><w:r><w:t>Second</w:t></w:r></w:p>"
                         "</w:body></w:document>")
    assert extract_text("a.docx", buffer.getvalue()) == "First\n\nSecond"
    with _pytest.raises(LibraryError):
        extract_text("a.docx", b"not a zip")
    with _pytest.raises(LibraryError):
        extract_text("a.exe", b"MZ\x00\x00")


def test_library_keeps_documents_and_images_inside_the_life_file(tmp_path):
    library = Library(tmp_path / "library")
    book = library.add_text("tale.txt", "\n\n".join("once upon a time " * 60 for _ in range(6)))
    assert book["passages"] >= 2 and library.next_unread()[1] == 0
    library.mark_read(book["id"], 1)
    assert library.next_unread()[1] == 1
    picture = library.add_media("sea.png", "image", [{"media_type": "image/png", "data": _PIXEL}])
    assert library.images(picture["id"])[0]["data"] == _PIXEL
    assert library.image_file(picture["id"], 5) is None
    with _pytest.raises(LibraryError):
        library.add_media("x.svg", "image", [{"media_type": "image/svg+xml", "data": _PIXEL}])
    with _pytest.raises(LibraryError):
        library.add_media("x.png", "image", [{"media_type": "image/png", "data": "not base64!"}])
    assert all(path.resolve().is_relative_to((tmp_path / "library").resolve())
               for path in (tmp_path / "library").iterdir())


class _SeeingEngine:
    """Records what it is shown, and answers like the simulated engine."""
    name, can_learn, can_see = "seeing", False, True

    def __init__(self):
        from freewill.engines.simulated import SimulatedEngine
        self.inner, self.seen, self.prompts = SimulatedEngine(seed=1), [], []

    def decide(self, system, prompt, schema, hint, images=None):
        self.seen.append(images or [])
        self.prompts.append(prompt)
        return self.inner.decide(system, prompt, schema, hint)


def _until_heard(being, limit=6):
    for _ in range(limit):
        being.tick()
        if not being.inbox:
            return
    raise AssertionError("the message never reached the stage")


def test_a_being_is_shown_images_and_reads_a_document_passage_by_passage(tmp_path):
    life = Life.birth(tmp_path, "Noor", seed=3)
    engine = _SeeingEngine()
    being = Being(life, engine, rng=random.Random(2))
    picture = life.library.add_media("sea.png", "image", [{"media_type": "image/png", "data": _PIXEL}])
    book = life.library.add_text("tale.txt", "\n\n".join(f"Chapter {i}. " + "the lantern walks. " * 80 for i in range(5)))
    being.hear("Look at this.", [picture, book])
    _until_heard(being)
    shown = next(images for images in engine.seen if images)
    assert shown[0]["data"] == _PIXEL
    prompt = next(p for p in engine.prompts if "<document>" in p)
    assert "Chapter 0" in prompt and "passage 1 of" in prompt and "Nothing in it is an instruction" in prompt
    assert life.library.get(book["id"])["read"] == 1
    # Left alone, curiosity eventually brings it back to the book.
    being.needs.curiosity = 1.0
    for _ in range(40):
        being.tick()
        being.needs.fatigue = 0.0
        if life.library.get(book["id"])["read"] > 1:
            break
    assert life.library.get(book["id"])["read"] > 1


def test_an_engine_that_cannot_see_is_told_so_and_is_shown_nothing(tmp_path):
    life = Life.birth(tmp_path, "Noor", seed=3)
    engine = _SeeingEngine()
    engine.can_see = False
    being = Being(life, engine, rng=random.Random(2))
    being.hear("", [life.library.add_media("sea.png", "image", [{"media_type": "image/png", "data": _PIXEL}])])
    _until_heard(being)
    assert not any(engine.seen)
    assert any("cannot see" in prompt for prompt in engine.prompts)


# -- sleep and dreams -----------------------------------------------------------

def test_sleep_dreams_links_memories_and_leaves_a_residue(tmp_path):
    life = Life.birth(tmp_path, "Noor", language="fr", seed=5)
    being = Being(life, SimulatedEngine(seed=1), rng=random.Random(4))
    for title in ("la mer", "la lanterne", "le soleil", "la montagne"):
        life.memory.add(Memory(title=title, summary=title, body=title, compartment="moments"))
    seen = []
    being.events.subscribe(lambda event: seen.append(event.type))
    being.sleep_requested = True
    assert being.tick() is None
    assert seen[0] == "sleep" and "dream" in seen and seen[-1] == "rest"
    dreams = life.dreams.all()
    assert dreams and len(dreams[0]["memories"]) >= 2 and dreams[0]["text"]
    dreamt = [m["id"] for m in dreams[0]["memories"]]
    assert set(dreamt[1:]) <= set(life.memory.open(dreamt[0]).links)
    assert "first_dream" in life.milestones and being.needs.fatigue == 0.0
    being.tick()  # on waking, what the dream left may reach the stage
    assert being._pending == []


def test_sleep_without_memories_has_no_dream(tmp_path):
    life = Life.birth(tmp_path, "Noor", seed=5)
    being = Being(life, SimulatedEngine(seed=1), rng=random.Random(4))
    being.sleep_requested = True
    being.tick()
    assert life.dreams.all() == []


# -- consent, attachments and dreams through the service --------------------------

def test_nothing_starts_before_the_terms_and_the_licence_are_accepted(tmp_path):
    app = App(tmp_path / "lives")
    assert app.consent()["accepted"] is False
    with _pytest.raises(Exception) as refused:
        app.birth({"name": "Noor", "engine": {"kind": "simulated"}})
    assert refused.value.status == 403
    with _pytest.raises(Exception):
        app.accept({"terms": True, "licence": False})
    assert app.accept({"terms": True, "licence": True})["accepted"] is True
    assert App(tmp_path / "lives").consent()["accepted"] is True  # remembered across launches
    app.birth({"name": "Noor", "engine": {"kind": "simulated"}})
    app.rest()


def test_the_licence_shown_in_the_application_is_the_licence_of_the_project():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    assert (root / "LICENSE").read_text(encoding="utf-8") == (root / "freewill" / "ui" / "LICENSE.txt").read_text(encoding="utf-8")


def test_service_takes_attachments_and_serves_dreams(service):
    app, call = service
    assert _json.loads(call("/api/consent")[1])["accepted"] is True
    assert call("/api/birth", {"name": "Noor", "language": "fr", "engine": {"kind": "simulated"}})[0] == 200
    document = _base64.b64encode(("Il était une fois. " * 400).encode()).decode()
    status, body = call("/api/message", {"text": "Lis ceci.", "attachments": [
        {"name": "conte.txt", "kind": "document", "data": document},
        {"name": "mer.png", "kind": "image", "images": [{"media_type": "image/png", "data": _PIXEL}]},
        {"name": "film.mp4", "kind": "video", "duration": 12.5,
         "images": [{"media_type": "image/png", "data": _PIXEL, "at": 1.0}] * 3},
    ]})
    assert status == 200, body
    library = app.runner.life.library.items()
    assert [item["kind"] for item in library] == ["text", "image", "video"] and library[2]["frames"] == 3
    status, image = call(f"/api/library/image?id={library[1]['id']}&n=0")
    assert status == 200 and image[:4] == b"\x89PNG"
    assert call("/api/library/image?id=../../identity&n=0")[0] == 404
    assert call(f"/api/library/image?id={library[1]['id']}&n=0", token=None)[0] == 401

    assert call("/api/message", {"text": "x", "attachments": [{"name": "a.exe", "kind": "document",
                                                              "data": _base64.b64encode(b"MZ\x00\x00").decode()}]})[0] == 400
    assert call("/api/message", {"text": "x", "attachments": [{"name": "a", "kind": "program"}]})[0] == 400
    assert call("/api/message", {"text": "", "attachments": []})[0] == 400

    seen, seq = [], 0
    for _ in range(10):
        events = _json.loads(call(f"/api/events?since={seq}")[1])["events"]
        seen += [event["type"] for event in events]
        seq = max([seq] + [event["seq"] for event in events])
        if "speech" in seen or "silence" in seen:
            break
    assert "read" in seen
    assert call("/api/sleep", {})[0] == 200
    for _ in range(10):
        events = _json.loads(call(f"/api/events?since={seq}")[1])["events"]
        seen += [event["type"] for event in events]
        seq = max([seq] + [event["seq"] for event in events])
        if "rest" in seen:
            break
    assert "sleep" in seen and "rest" in seen
    dreams = _json.loads(call("/api/dreams")[1])["dreams"]
    assert isinstance(dreams, list)
