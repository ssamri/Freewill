"""H4: Freewill's own neural network, whose weights a life really rewrites and whose size really grows.

What this is: a small transformer that reads and predicts text one byte at a
time. It is born with random weights, inside the life file. While the being
is awake, what it lives is written down as text. During sleep the network is
trained on that text by gradient descent, measured on passages it was never
trained on, and kept only if it predicts them better without predicting the
older ones worse; otherwise the weights of before are restored, to the bit.
When enough new text has been lived, and if growth is allowed, one layer is
added. The new layer starts as the identity, so the network predicts exactly
what it predicted before, with more parameters to learn with. The count of
parameters reported here is the count of numbers in the weights file.

What this is not: it does not speak or decide for the being. At this size it
cannot. The being still thinks with its engine, whose weights are untouched.
It needs PyTorch, which is optional: without it nothing is trained and the
interface says so. Nothing here measures or implies experience.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

FOLDER = "own_model"
BLOCK = 96                 # bytes of context
BATCH = 16
BIRTH = {"layers": 2, "width": 192, "heads": 4}
RATE = 3e-4
HELD_EVERY = 10            # one passage in ten is never trained on
MIN_PASSAGES = 20
MIN_GAIN = 0.001           # nats per byte on held-out passages
MAX_FORGETTING = 0.05      # nats per byte on older held-out passages
GROW_EVERY_BYTES = 20_000  # one more layer for this much newly lived text
MAX_CORPUS = 20_000_000
RULES_VERSION = "h4-own-0.1"

_torch = None
_classes = None


def torch_or_none():
    global _torch
    if _torch is None:
        try:
            import torch
            _torch = torch
        except Exception:  # not installed, or not loadable on this machine
            _torch = False
    return _torch or None


def _net(layers: int, width: int, heads: int):
    global _classes
    torch = torch_or_none()
    nn = torch.nn
    if _classes is None:
        class Block(nn.Module):
            def __init__(self, width, heads):
                super().__init__()
                self.ln1, self.ln2 = nn.LayerNorm(width), nn.LayerNorm(width)
                self.attn = nn.MultiheadAttention(width, heads, batch_first=True)
                self.up, self.down = nn.Linear(width, 4 * width), nn.Linear(4 * width, width)

            def forward(self, x, mask):
                y = self.ln1(x)
                x = x + self.attn(y, y, y, attn_mask=mask, need_weights=False)[0]
                return x + self.down(nn.functional.gelu(self.up(self.ln2(x))))

            def silence(self):
                """Make this layer the identity: what it adds to the stream starts at zero."""
                for tensor in (self.attn.out_proj.weight, self.attn.out_proj.bias, self.down.weight, self.down.bias):
                    nn.init.zeros_(tensor)

        class Net(nn.Module):
            def __init__(self, layers, width, heads):
                super().__init__()
                self.tok, self.pos = nn.Embedding(256, width), nn.Embedding(BLOCK, width)
                self.blocks = nn.ModuleList(Block(width, heads) for _ in range(layers))
                self.ln = nn.LayerNorm(width)
                for table in (self.tok, self.pos):  # small at birth, so that its first guesses are near uniform
                    nn.init.normal_(table.weight, std=0.02)

            def forward(self, idx):
                length = idx.shape[1]
                x = self.tok(idx) + self.pos(torch.arange(length))
                mask = torch.triu(torch.ones(length, length, dtype=torch.bool), 1)
                for block in self.blocks:
                    x = block(x, mask)
                return self.ln(x) @ self.tok.weight.T

        _classes = (Block, Net)
    return _classes[1](layers, width, heads)


def count(net) -> int:
    return sum(p.numel() for p in net.parameters())


def weights_hash(net) -> str:
    sha = hashlib.sha256()
    for name, tensor in sorted(net.state_dict().items()):
        sha.update(name.encode("utf-8"))
        sha.update(tensor.detach().cpu().numpy().tobytes())
    return sha.hexdigest()


class OwnModel:
    def __init__(self, life_path: Path, seed: int, emit=None) -> None:
        self.root = Path(life_path) / FOLDER
        self.seed = int(seed)
        self.emit = emit or (lambda *args, **kwargs: None)
        self.grow_every = GROW_EVERY_BYTES
        self.meta = {"rules": RULES_VERSION, "config": dict(BIRTH), "jobs": [], "growths": [],
                     "trained_bytes": 0, "grown_at_bytes": 0}
        if (self.root / "manifest.json").exists():
            try:
                self.meta.update(json.loads((self.root / "manifest.json").read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass

    # -- awake: what is lived is written down ------------------------------------------------

    def live(self, texts: list[str]) -> None:
        lines = [" ".join(str(text).split()) for text in texts if text and str(text).strip()]
        if not lines:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        corpus = self.root / "corpus.txt"
        if corpus.exists() and corpus.stat().st_size > MAX_CORPUS:
            return
        with corpus.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")

    def corpus_bytes(self) -> int:
        corpus = self.root / "corpus.txt"
        return corpus.stat().st_size if corpus.exists() else 0

    # -- the weights -------------------------------------------------------------------------

    def _load(self):
        torch = torch_or_none()
        config = self.meta["config"]
        torch.manual_seed(self.seed)
        net = _net(config["layers"], config["width"], config["heads"])
        path = self.root / "model.pt"
        if path.exists():
            net.load_state_dict(torch.load(path, weights_only=True))
        return net

    def _store(self, net) -> None:
        torch = torch_or_none()
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / "model.pt"
        if path.exists():  # the weights of before are kept, so that a person can go back to them
            shutil.copyfile(path, self.root / "previous.pt")
            self.meta["previous_config"] = dict(self.meta.get("stored_config") or self.meta["config"])
        temporary = self.root / "model.pt.tmp"
        torch.save(net.state_dict(), temporary)
        os.replace(temporary, path)
        self.meta["stored_config"] = dict(self.meta["config"])
        self.meta["parameters"] = count(net)
        self.meta["weights_sha256"] = weights_hash(net)

    def _save_meta(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.root / "manifest.json.tmp"
        temporary.write_text(json.dumps(self.meta, indent=1), encoding="utf-8")
        os.replace(temporary, self.root / "manifest.json")

    def _passages(self, upto: int | None = None):
        """The lived text cut into fixed passages. One in ten, always the same ones, is held out."""
        torch = torch_or_none()
        data = (self.root / "corpus.txt").read_bytes() if (self.root / "corpus.txt").exists() else b""
        if upto is not None:
            data = data[:upto]
        size = BLOCK + 1
        rows = [list(data[i:i + size]) for i in range(0, len(data) - size + 1, size)]
        if not rows:
            empty = torch.zeros((0, size), dtype=torch.long)
            return empty, empty
        tensor = torch.tensor(rows, dtype=torch.long)
        held = torch.arange(len(rows)) % HELD_EVERY == HELD_EVERY - 1
        return tensor[~held], tensor[held]

    @staticmethod
    def _loss(net, passages) -> float | None:
        torch = torch_or_none()
        if len(passages) == 0:
            return None
        net.eval()
        total = 0.0
        with torch.no_grad():
            for start in range(0, len(passages), 64):
                batch = passages[start:start + 64]
                logits = net(batch[:, :-1])
                total += torch.nn.functional.cross_entropy(
                    logits.reshape(-1, 256), batch[:, 1:].reshape(-1), reduction="sum").item()
        return round(total / (len(passages) * BLOCK), 6)

    # -- asleep: training, and growth --------------------------------------------------------

    def sleep(self, steps: int = 60, grow: bool = False, ceiling: int = 5_000_000) -> dict | None:
        torch = torch_or_none()
        if torch is None:
            self.emit("learning_unavailable", module="own_model", reason="no_torch")
            return None
        train, held = self._passages()
        if len(train) + len(held) < MIN_PASSAGES or len(held) == 0:
            self.emit("learning_unavailable", module="own_model", reason="too_little_text")
            return None
        started = time.monotonic()
        job = len(self.meta["jobs"]) + 1
        net = self._load()
        if not (self.root / "model.pt").exists():
            self._store(net)  # the weights it was born with
        _old_train, old_held = self._passages(self.meta["trained_bytes"])
        before = {name: tensor.clone() for name, tensor in net.state_dict().items()}
        hash_before, parameters = weights_hash(net), count(net)
        held_before, old_before = self._loss(net, held), self._loss(net, old_held)

        torch.manual_seed(self.seed * 1000 + job)
        optimiser = torch.optim.AdamW(net.parameters(), lr=RATE)
        net.train()
        for _ in range(int(steps)):
            batch = train[torch.randint(len(train), (BATCH,))]
            loss = torch.nn.functional.cross_entropy(net(batch[:, :-1]).reshape(-1, 256), batch[:, 1:].reshape(-1))
            optimiser.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            optimiser.step()
        held_after, old_after = self._loss(net, held), self._loss(net, old_held)
        gain = held_before - held_after
        forgetting = (old_after - old_before) if old_before is not None else 0.0
        accepted = gain >= MIN_GAIN and forgetting <= MAX_FORGETTING
        delta = sum(((net.state_dict()[name] - tensor).double() ** 2).sum().item()
                    for name, tensor in before.items() if tensor.is_floating_point()) ** 0.5
        if accepted:
            self._store(net)
        else:  # rejected: the weights of before are kept, to the bit
            net.load_state_dict(before)
        corpus = self.corpus_bytes()
        report = {
            "rules": RULES_VERSION, "job": job, "training_method": "gradient descent on lived text, byte level",
            "decision": "accepted" if accepted else "rejected", "steps": int(steps),
            "checkpoint_before": hash_before, "checkpoint_after": weights_hash(net),
            "trainable_parameters": parameters, "layers": self.meta["config"]["layers"],
            "weight_delta_l2": round(delta if accepted else 0.0, 6),
            "heldout_loss_before": held_before, "heldout_loss_after": held_after if accepted else held_before,
            "heldout_loss_candidate": held_after, "old_loss_before": old_before, "old_loss_candidate": old_after,
            "heldout_passages": int(len(held)), "train_passages": int(len(train)), "corpus_bytes": corpus,
            "seconds": round(time.monotonic() - started, 2), "device": "cpu", "torch": torch.__version__,
            "engine_weights_changed": False, "speaks_for_the_being": False}
        self.meta["jobs"] = (self.meta["jobs"] + [report])[-200:]
        self.meta["trained_bytes"] = corpus
        self.emit("own_model_job", **report)
        if accepted and grow and corpus - self.meta["grown_at_bytes"] >= self.grow_every:
            self._grow(net, held, ceiling)
        self._save_meta()
        return report

    def _grow(self, net, held, ceiling: int) -> dict | None:
        """Add one layer that starts as the identity: same predictions, more parameters to learn with."""
        config = self.meta["config"]
        before_parameters, before_loss = count(net), self._loss(net, held)
        grown = _net(config["layers"] + 1, config["width"], config["heads"])
        if count(grown) > ceiling:
            self.emit("own_model_growth", decision="refused", reason="ceiling", parameters=before_parameters,
                      ceiling=int(ceiling))
            return None
        state = grown.state_dict()
        state.update(net.state_dict())  # every existing weight is carried over unchanged
        grown.load_state_dict(state)
        grown.blocks[-1].silence()
        after_loss = self._loss(grown, held)
        preserved = abs(after_loss - before_loss) < 1e-4
        record = {"decision": "accepted" if preserved else "rejected", "layers_before": config["layers"],
                  "layers_after": config["layers"] + 1, "parameters_before": before_parameters,
                  "parameters_after": count(grown), "heldout_loss_before": before_loss,
                  "heldout_loss_after": after_loss, "function_preserved": preserved,
                  "corpus_bytes": self.corpus_bytes(), "after_job": len(self.meta["jobs"])}
        if preserved:
            config["layers"] += 1
            self._store(grown)
            self.meta["grown_at_bytes"] = record["corpus_bytes"]
        self.meta["growths"] = (self.meta["growths"] + [record])[-200:]
        self.emit("own_model_growth", **record)
        return record

    # -- a person's controls -----------------------------------------------------------------

    def rollback(self) -> bool:
        """Return to the weights of before the last accepted change. A person can always ask for this."""
        previous = self.root / "previous.pt"
        if not previous.exists():
            return False
        os.replace(previous, self.root / "model.pt")
        self.meta["config"] = dict(self.meta.get("previous_config") or self.meta["config"])
        self.meta["stored_config"] = dict(self.meta["config"])
        if torch_or_none():
            net = self._load()
            self.meta["parameters"], self.meta["weights_sha256"] = count(net), weights_hash(net)
        self.emit("learning_rollback", module="own_model", parameters=self.meta.get("parameters"))
        self._save_meta()
        return True

    def sample(self, prompt: str = "", length: int = 160) -> str | None:
        """What the network writes when asked to continue a text. A look at what it learned, nothing more."""
        torch = torch_or_none()
        if torch is None or not (self.root / "model.pt").exists():
            return None
        net = self._load()
        net.eval()
        generator = torch.Generator().manual_seed(self.seed)
        out = list((prompt or "\n").encode("utf-8"))[-BLOCK:]
        with torch.no_grad():
            for _ in range(max(1, min(int(length), 400))):
                logits = net(torch.tensor([out[-BLOCK:]]))[0, -1] / 0.8
                out.append(int(torch.multinomial(torch.softmax(logits, -1), 1, generator=generator)))
        return bytes(out).decode("utf-8", errors="replace")

    def public(self) -> dict:
        jobs, growths = self.meta["jobs"], self.meta["growths"]
        return {"rules": RULES_VERSION, "torch": bool(torch_or_none()), "born": (self.root / "model.pt").exists(),
                "parameters": self.meta.get("parameters"), "layers": self.meta["config"]["layers"],
                "width": self.meta["config"]["width"], "weights_sha256": self.meta.get("weights_sha256"),
                "corpus_bytes": self.corpus_bytes(), "jobs": jobs[-10:], "jobs_total": len(jobs),
                "jobs_accepted": sum(1 for job in jobs if job["decision"] == "accepted"),
                "growths": growths[-10:], "can_roll_back": (self.root / "previous.pt").exists(),
                "engine_weights_changed": False, "speaks_for_the_being": False}
