"""H4, the engine that a life adapts: corpus, nightly cycle, checkpoints, conversion, runtime pin.

The training tests run on a tiny Qwen3-shaped model with random weights and a tokenizer trained here,
so that they run anywhere in seconds. They check the mechanics, not that a real model learns anything:
that is what tools/engine_e2e.py and the "embedded engine end to end" workflow are for.
"""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path

import pytest

from freewill import models, runtime
from freewill.core.life import Life
from freewill.learning import engine as engine_learning
from freewill.learning.engine import EngineLearning, EngineLearningError, gather, held_out

TRAINING = all(__import__("importlib").util.find_spec(name) for name in ("torch", "peft", "transformers", "gguf", "tokenizers"))
needs_training = pytest.mark.skipif(not TRAINING, reason="needs torch, peft, transformers, gguf and tokenizers")

LINES = [
    ("The lighthouse of Kerran is green.", "Green, then. I will remember the lighthouse of Kerran."),
    ("Lumo is the lemon tree with blue lemons.", "Lumo gives blue lemons. That is lovely."),
    ("Pilou the fox sleeps under Lumo.", "Pilou sleeps under the blue lemon tree."),
    ("The ferry leaves Maelis on Tuesday.", "On Tuesday, from Maelis."),
    ("Ilse bakes bread with seaweed.", "Seaweed bread from Ilse."),
    ("Tobin is the lighthouse keeper's cat.", "Tobin the cat lives at the lighthouse."),
    ("Kerran has one road to the lighthouse.", "One road, from the harbour to the lighthouse."),
    ("Sam teaches music at the school.", "You teach music at the school of Kerran."),
    ("The lighthouse is called Old Brannoc.", "Old Brannoc, the green lighthouse."),
    ("In winter the blue lemons turn purple.", "Purple in winter, blue the rest of the year."),
    ("Joran fishes from the Little Heron.", "The Little Heron is Joran's boat."),
    ("The festival lights lanterns in June.", "Lanterns on the road in June."),
    ("Old Brannoc stands on the north cliff.", "On the north cliff of Kerran."),
    ("The school has eleven pupils.", "Eleven pupils at the school."),
    ("Pilou was your first friend.", "Pilou the fox, my first friend."),
    ("The ferry comes back on Friday.", "It comes back on Friday."),
    ("Ilse opens her bakery at six.", "At six in the morning."),
    ("Tobin is afraid of Pilou.", "The cat is afraid of the fox."),
    ("Lumo grows by the garden wall.", "By the wall of the garden."),
    ("The Little Heron is red.", "A red boat."),
    ("The road is lined with stones.", "Stones along the road."),
    ("Sam plays the violin.", "You play the violin."),
    ("Maelis is a busy harbour.", "A busy harbour."),
    ("Old Brannoc is two hundred years old.", "Two hundred years."),
]


def write_events(life_path: Path, lines) -> None:
    with (life_path / "events.log").open("a", encoding="utf-8") as log:
        for heard, said in lines:
            log.write(json.dumps({"type": "heard", "time": "t", "text": heard}) + "\n")
            log.write(json.dumps({"type": "stage", "time": "t", "source": "message", "text": heard}) + "\n")
            log.write(json.dumps({"type": "decision", "time": "t", "accepted": True}) + "\n")
            log.write(json.dumps({"type": "speech", "time": "t", "text": said, "spontaneous": False}) + "\n")
            log.write(json.dumps({"type": "stage", "time": "t", "source": "drift", "text": "x"}) + "\n")
            log.write(json.dumps({"type": "speech", "time": "t", "text": "a thought aloud", "spontaneous": True}) + "\n")


@pytest.fixture
def life(tmp_path):
    return Life.birth(tmp_path / "lives", "Ada", engine={"kind": "embedded", "model": "toy"}, seed=1)


TOY_MODEL = {"id": "toy", "name": "Toy Qwen3", "architecture": "qwen3", "trainable": {"files": []}}


@pytest.fixture(scope="module")
def toy_base(tmp_path_factory):
    if not TRAINING:
        pytest.skip("training libraries missing")
    return build_toy_base(tmp_path_factory.mktemp("toy-base"))


def build_toy_base(folder: Path) -> Path:
    import torch
    from tokenizers import Tokenizer, models as tmodels, pre_tokenizers, trainers, decoders
    from transformers import PreTrainedTokenizerFast, Qwen3Config, Qwen3ForCausalLM
    texts = [a + " " + b for a, b in LINES] + [t for v in json.loads(engine_learning.REFERENCE_PATH.read_text())["general"].values() for t in v]
    tok = Tokenizer(tmodels.BPE(unk_token="<unk>"))
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    tok.train_from_iterator(texts * 3, trainers.BpeTrainer(vocab_size=600, special_tokens=["<unk>", "<|im_start|>", "<|im_end|>"],
                                                         initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
    fast = PreTrainedTokenizerFast(tokenizer_object=tok, unk_token="<unk>", eos_token="<|im_end|>")
    fast.chat_template = ("{% for m in messages %}<|im_start|>{{ m['role'] }}\n{{ m['content'] }}<|im_end|>\n{% endfor %}")
    fast.save_pretrained(folder)
    torch.manual_seed(0)
    config = Qwen3Config(vocab_size=len(fast), hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                         num_attention_heads=4, num_key_value_heads=2, head_dim=16, max_position_embeddings=512,
                         tie_word_embeddings=True)
    Qwen3ForCausalLM(config).save_pretrained(folder)
    return folder


def bench_for(toy_base):
    from freewill.learning.lora import Workbench
    return Workbench(toy_base, device="cpu")


# -- the corpus ----------------------------------------------------------------------------------

def test_the_corpus_is_what_was_said_and_answered_and_held_out_items_are_never_trained_on(life):
    write_events(life.path, LINES[:6])
    items, offset, skipped = gather(life.path)
    assert [i["messages"][0]["content"] for i in items] == [a for a, _ in LINES[:6]]
    assert all(i["messages"][1]["content"] != "a thought aloud" for i in items)  # spontaneous speech is not a reply
    learning = EngineLearning(life.path)
    first = learning.collect()
    assert first["added_train"] + first["added_held_out"] == 6
    again = learning.collect()  # nothing new was lived
    assert again["added_train"] == again["added_held_out"] == 0
    write_events(life.path, LINES[:2])  # the same exchanges again are not new items
    assert learning.collect()["skipped"].get("duplicate") == 2
    train = {r["sha256"] for r in learning._rows("corpus.jsonl")}
    held = {r["sha256"] for r in learning._rows("heldout.jsonl")}
    assert not train & held
    assert all(held_out(r) for r in learning._rows("heldout.jsonl"))
    assert any(row["kind"] == "corpus" for row in learning.ledger())


def test_turning_engine_learning_on_needs_a_name_and_is_recorded(life):
    learning = EngineLearning(life.path)
    assert learning.settings.enabled is False
    with pytest.raises(EngineLearningError):
        learning.configure({"enabled": True})
    settings = learning.configure({"enabled": True, "rank": 1000}, who="Sam")
    assert settings.enabled and settings.approved_by == "Sam" and settings.rank == 64
    assert learning.ledger()[-1]["kind"] == "settings"


def test_a_night_with_too_little_lived_trains_nothing(life):
    learning = EngineLearning(life.path)
    learning.configure({"enabled": True}, who="Sam")
    write_events(life.path, LINES[:2])
    row = learning.night(TOY_MODEL, None, workbench=object())
    assert row["kind"] == "skipped" and row["reason"] == "not_enough_lived"
    assert not (learning.root / "adapters").exists()


# -- a night on the toy base -------------------------------------------------------------------------

@needs_training
def test_a_night_trains_measures_converts_and_loads_only_what_helps(life, toy_base, monkeypatch):
    learning = EngineLearning(life.path)
    learning.configure({"enabled": True, "steps": 60, "lr": 0.01, "rank": 4}, who="Sam")
    write_events(life.path, LINES)
    monkeypatch.setattr(engine_learning, "MAX_FORGETTING", 10.0)  # a random toy forgets freely; the rule is tested below
    calls = []
    row = learning.night(TOY_MODEL, None, workbench=bench_for(toy_base),
                         runtime_check=lambda path, texts: calls.append((path, len(texts))) or {"ran": True, "adapter_loaded": True})
    assert row["decision"] == "accepted", row
    assert row["base_weights_unchanged"] and row["candidates"]["candidate"]["verdict"]["gain"] >= engine_learning.MIN_GAIN
    assert calls and calls[0][0].name == "adapter.gguf"
    active = learning.active("toy")
    folder = Path(active["folder"])
    manifest = json.loads((folder / "manifest.json").read_text())
    assert manifest["gguf_sha256"] == active["sha256"] == hashlib.sha256((folder / "adapter.gguf").read_bytes()).hexdigest()
    assert manifest["adapter_parameters"] > 0 and manifest["delta_total_frobenius"] > 0
    assert json.loads((folder / "weights_delta.json").read_text())["modules"]  # every change of weights, module by module
    from freewill.learning.gguf_lora import check
    found = check(folder / "adapter.gguf", "qwen3")
    assert found["tensors"] == 2 * 7 * 2  # A and B, seven matrices, two layers
    # Items used are marked; the corpus remembers which night used them.
    assert all(r["night"] == row["version"] for r in learning._rows("corpus.jsonl"))
    # An adapter belongs to its base model.
    assert learning.active("another-model") is None


@needs_training
def test_a_night_that_does_not_help_or_forgets_leaves_nothing_behind(life, toy_base, monkeypatch):
    learning = EngineLearning(life.path)
    learning.configure({"enabled": True, "steps": 2, "lr": 0.0, "rank": 2}, who="Sam")
    write_events(life.path, LINES)
    row = learning.night(TOY_MODEL, None, workbench=bench_for(toy_base))
    assert row["decision"] == "rejected" and "no_gain_on_held_out" in row["candidates"]["candidate"]["verdict"]["reasons"]
    assert not (learning.root / "adapters").exists() and learning.active("toy") is None
    # The forgetting rule: a candidate that predicts the reference texts worse than the base is refused.
    learning2 = EngineLearning(Life.birth(life.path.parent, "Bea", seed=2).path)
    learning2.configure({"enabled": True, "steps": 40, "lr": 0.02, "rank": 4}, who="Sam")
    write_events(learning2.life_path, LINES)
    monkeypatch.setattr(engine_learning, "MAX_FORGETTING", -10.0)
    row = learning2.night(TOY_MODEL, None, workbench=bench_for(toy_base))
    assert row["decision"] == "rejected" and "forgets_reference" in row["candidates"]["candidate"]["verdict"]["reasons"]


@needs_training
def test_checkpoints_can_be_restored_and_a_tampered_adapter_is_never_loaded(life, toy_base, monkeypatch):
    learning = EngineLearning(life.path)
    learning.configure({"enabled": True, "steps": 60, "lr": 0.01, "rank": 4}, who="Sam")
    write_events(life.path, LINES)
    monkeypatch.setattr(engine_learning, "MAX_FORGETTING", 10.0)
    version = learning.night(TOY_MODEL, None, workbench=bench_for(toy_base))["version"]
    learning.restore(None, who="Sam")
    assert learning.active("toy") is None
    learning.restore(version, who="Sam")
    assert learning.active("toy")["version"] == version
    with pytest.raises(EngineLearningError):
        learning.restore("a9999")
    gguf = learning.root / "adapters" / version / "adapter.gguf"
    gguf.write_bytes(gguf.read_bytes()[:-8] + b"tampered")
    assert learning.active("toy") is None
    assert learning.ledger()[-1]["kind"] == "integrity_failure"
    assert [r["kind"] for r in learning.ledger()].count("restore") == 2


@needs_training
def test_growth_preserves_the_function_and_is_kept_only_if_it_does_better(life, toy_base, monkeypatch):
    bench = bench_for(toy_base)
    seq = bench.tokens([{"text": "The lighthouse of Kerran is green."}])
    bench.fresh("small", 2, seed=1)
    bench.train("small", seq, steps=5, lr=0.05)
    bench.copy("small", "big", rank=4)
    assert bench.parameters("big") == 2 * bench.parameters("small")
    assert abs(bench.losses("small", seq)[0]["nll"] - bench.losses("big", seq)[0]["nll"]) < 1e-5
    # In a night: growth considered, recorded with both sizes, decided by the held-out rule.
    learning = EngineLearning(life.path)
    learning.configure({"enabled": True, "steps": 40, "lr": 0.01, "rank": 2, "growth": True, "max_rank": 4}, who="Sam")
    write_events(life.path, LINES)
    monkeypatch.setattr(engine_learning, "MAX_FORGETTING", 10.0)
    row = learning.night(TOY_MODEL, None, workbench=bench_for(toy_base))
    growth = row["growth"]
    assert growth["considered"] and growth["rank_before"] == 2 and growth["rank_after"] == 4
    assert growth["parameters_after"] == 2 * growth["parameters_before"]
    assert growth["decision"] in ("accepted", "rejected")
    # Over budget: not even trained.
    learning.configure({"max_adapter_parameters": 1}, who="Sam")
    write_events(life.path, [(a + " again", b + " again") for a, b in LINES])
    row = learning.night(TOY_MODEL, None, workbench=bench_for(toy_base))
    assert row["growth"]["decision"] in ("over_budget", "at_max_rank")


@needs_training
def test_the_lab_compares_base_adapted_and_controls_item_by_item(life, toy_base, monkeypatch):
    from freewill.learning import compare
    learning = EngineLearning(life.path)
    learning.configure({"enabled": True, "steps": 60, "lr": 0.01, "rank": 4}, who="Sam")
    write_events(life.path, LINES + [(a + " Truly.", b + " Truly.") for a, b in LINES])
    monkeypatch.setattr(engine_learning, "MAX_FORGETTING", 10.0)
    assert learning.night(TOY_MODEL, None, workbench=bench_for(toy_base))["decision"] == "accepted"
    found = compare.compare(life.path, TOY_MODEL, None, workbench=bench_for(toy_base))
    assert set(found["conditions"]) == {"base", "adapted", "control_shuffled", "control_random"}
    n = len(found["held_out_sha256"])
    assert n >= 6 and all(len(v) == n for v in found["per_item"].values())
    sizes = {k: v["delta_frobenius"] for k, v in found["conditions"].items()}
    assert sizes["base"] == 0 and abs(sizes["control_random"] - sizes["adapted"]) / sizes["adapted"] < 0.05
    rows = {(c["condition"], c["reference"]): c for c in found["comparisons"]}
    assert rows[("adapted", "base")]["n_units"] == n and rows[("adapted", "base")]["mean_difference"] < 0


# -- the engine loads what was accepted --------------------------------------------------------------

def test_the_embedded_engine_starts_llama_server_with_the_adapter(tmp_path, monkeypatch):
    from freewill.engines import embedded
    model_file = tmp_path / "m.gguf"
    model_file.write_bytes(b"x")
    adapter = tmp_path / "adapter.gguf"
    adapter.write_bytes(b"y")
    seen = {}

    class Stop(Exception):
        pass

    def popen(command, **kwargs):
        seen["command"] = command
        raise Stop
    monkeypatch.setattr(embedded.subprocess, "Popen", popen)
    model = models.find("qwen3-1.7b")
    engine = embedded.EmbeddedEngine(model, model_file, runtime=tmp_path / "llama-server",
                                     adapter={"version": "a0001", "gguf": str(adapter), "sha256": "ab" * 32})
    assert "+adapter:a0001:" in engine.name and engine.can_learn
    with pytest.raises(Stop):
        engine._start()
    command = seen["command"]
    assert command[command.index("--lora-scaled") + 1] == str(adapter)
    assert "--reasoning-budget" in command
    plain = embedded.EmbeddedEngine(models.find("smolvlm2-2.2b"), model_file, runtime=tmp_path / "llama-server")
    assert plain.adapter is None and "adapter" not in plain.name and not plain.can_learn


# -- the catalogue and the runtime ----------------------------------------------------------------------

def test_qwen3_is_pinned_with_its_trainable_base_and_licence():
    model = models.find("qwen3-1.7b")
    assert model["licence"] == "Apache-2.0" and model["architecture"] == "qwen3" and model["learns"]
    assert len(model["sha256"]) == 64 and model["size"] > 1_000_000_000 and model["revision"]
    files = model["trainable"]["files"]
    assert {"config.json", "tokenizer.json", "model-00001-of-00002.safetensors"} <= {f["name"] for f in files}
    assert all(len(f["sha256"]) == 64 and f["size"] > 0 for f in files)
    store = models.ModelStore(Path("/nonexistent"))
    url = store._url(model, "base/config.json", "training")
    assert url == f"https://huggingface.co/Qwen/Qwen3-1.7B/resolve/{model['trainable']['revision']}/config.json"
    assert store._url(model, model["file"], "inference").endswith(f"/resolve/{model['revision']}/{model['file']}")
    listed = next(m for m in store.listing() if m["id"] == "qwen3-1.7b")
    assert listed["training_size"] > 4_000_000_000 and "trainable" not in listed and not listed["training_installed"]


def test_the_runtime_pin_covers_each_desktop_system():
    pin = runtime.pin()
    assert pin["licence"] == "MIT" and pin["tag"].startswith("b")
    for key in ("win-x64", "linux-x64", "macos-arm64", "macos-x64"):
        asset = pin["assets"][key]
        assert len(asset["sha256"]) == 64 and asset["size"] > 1_000_000 and pin["tag"] in asset["name"]


def _archive(kind: str) -> bytes:
    files = {"llama-b1/llama-server": b"server", "llama-b1/llama-perplexity": b"ppl", "llama-b1/libllama.so.0.9.0": b"lib",
             "llama-b1/llama-quantize": b"not wanted", "llama-b1/LICENSE": b"MIT"}
    buffer = io.BytesIO()
    if kind == "tar":
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            for name, data in files.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
            link = tarfile.TarInfo("llama-b1/libllama.so.0")
            link.type, link.linkname = tarfile.SYMTYPE, "libllama.so.0.9.0"
            archive.addfile(link)
            evil = tarfile.TarInfo("../../evil.so")
            evil.size = 1
            archive.addfile(evil, io.BytesIO(b"x"))
    else:
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, data in {"llama-server.exe": b"s", "llama.dll": b"d", "llama-cli.exe": b"no", "LICENSE-LLVM-OpenMP": b"l"}.items():
                archive.writestr(name, data)
    return buffer.getvalue()


def test_the_runtime_is_unpacked_to_the_programs_it_needs_and_nothing_unchecked_is_kept(tmp_path, monkeypatch):
    raw = _archive("tar")
    pin = {"tag": "b1", "source": "https://example.invalid", "licence": "MIT",
           "assets": {"linux-x64": {"name": "llama-b1-bin-ubuntu-x64.tar.gz", "size": len(raw),
                                    "sha256": hashlib.sha256(raw).hexdigest()}}}
    monkeypatch.setattr(runtime, "pin", lambda: pin)

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    monkeypatch.setattr(runtime.urllib.request, "urlopen", lambda request, timeout: Response(raw))
    folder = runtime.install(target=tmp_path / "rt", key="linux-x64")
    names = sorted(p.name for p in folder.iterdir())
    assert names == ["LICENSE", "freewill_runtime.json", "libllama.so.0", "libllama.so.0.9.0", "llama-perplexity", "llama-server"]
    assert not (tmp_path / "evil.so").exists()
    # A different archive than the pinned one is refused, and nothing is installed.
    monkeypatch.setattr(runtime.urllib.request, "urlopen", lambda request, timeout: Response(raw[:-1] + b"!"))
    with pytest.raises(runtime.RuntimeFetchError):
        runtime.install(target=tmp_path / "rt2", key="linux-x64")
    assert not (tmp_path / "rt2").exists()
    zipped = io.BytesIO(_archive("zip"))
    out = tmp_path / "win"
    out.mkdir()
    runtime._unpack(zipped, "x.zip", out, windows=True)
    assert sorted(p.name for p in out.iterdir()) == ["LICENSE-LLVM-OpenMP", "llama-server.exe", "llama.dll"]
