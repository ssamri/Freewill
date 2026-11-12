"""The architecture of Freewill's own model, and the operations that change it.

    image or video frame ──▶ eye (SigLIP2 vision tower, frozen)
                         ──▶ bridge (pixel shuffle + two-layer MLP, trained by Freewill)
                         ──▶ vectors in the language model's own space
    text ─────────────────▶ language model (Qwen3 1.7B), adapted by low-rank adapters
                            and by whole layers that Freewill adds while it grows

The model is assembled from open pieces and its parameter count is the count
of numbers it computes with, measured here, never declared. Growth adds whole
decoder layers that start as the identity (their output projections are zero),
so the model predicts exactly what it predicted before and has more parameters
to learn with; growth is refused above the ceiling written in spec.json.

A tiny version of the same architecture, with random weights and a byte-level
tokenizer, exists for tests (`tiny()`): it checks the mechanics, never that a
real model learns anything.

Needs PyTorch and Transformers (the `lora` extra).
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import torch
from torch import nn

SPEC_PATH = Path(__file__).resolve().parent / "spec.json"
IMAGE_MEAN = (0.5, 0.5, 0.5)
IMAGE_STD = (0.5, 0.5, 0.5)


def load_spec(path: Path | None = None) -> dict:
    return json.loads(Path(path or SPEC_PATH).read_text(encoding="utf-8"))


# -- tokenizers -----------------------------------------------------------------

class ByteTokenizer:
    """One token per byte, plus an end token. For the tiny test model only."""

    vocab_size = 258
    eos_id = 256
    pad_id = 257
    has_chat_template = False

    def encode(self, text: str) -> list[int]:
        return list(text.encode("utf-8"))

    def decode(self, ids) -> str:
        return bytes(i for i in ids if i < 256).decode("utf-8", "replace")


class HFTokenizer:
    """A Transformers tokenizer seen through the small interface the model uses."""

    def __init__(self, tokenizer) -> None:
        self.inner = tokenizer
        self.eos_id = tokenizer.eos_token_id
        self.pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
        self.vocab_size = len(tokenizer)
        self.has_chat_template = bool(getattr(tokenizer, "chat_template", None))

    def encode(self, text: str) -> list[int]:
        return self.inner.encode(text, add_special_tokens=False)

    def decode(self, ids) -> str:
        return self.inner.decode(list(ids), skip_special_tokens=True)


# -- pieces ---------------------------------------------------------------------

class Bridge(nn.Module):
    """From the eye's patch vectors to vectors in the language model's space.

    Neighbouring patches are folded together (pixel shuffle), which divides the
    number of image tokens by shuffle², then a two-layer MLP maps them."""

    def __init__(self, vision_width: int, text_width: int, shuffle: int = 2, hidden: int | None = None) -> None:
        super().__init__()
        self.shuffle = shuffle
        folded = vision_width * shuffle * shuffle
        hidden = hidden or text_width
        self.norm = nn.LayerNorm(folded)
        self.up = nn.Linear(folded, hidden)
        self.down = nn.Linear(hidden, text_width)

    def forward(self, patches: torch.Tensor) -> torch.Tensor:
        batch, count, width = patches.shape
        side, s = int(math.isqrt(count)), self.shuffle
        if side * side != count or side % s:
            raise ValueError(f"{count} patches cannot be folded by {s}")
        x = patches.reshape(batch, side // s, s, side // s, s, width).permute(0, 1, 3, 2, 4, 5)
        x = x.reshape(batch, (side // s) ** 2, s * s * width)
        return self.down(nn.functional.gelu(self.up(self.norm(x))))


class LoRALinear(nn.Module):
    """A frozen linear layer with a trainable low-rank update beside it. B starts at zero: no change at birth."""

    def __init__(self, base: nn.Linear, rank: int, alpha: float) -> None:
        super().__init__()
        self.base = base
        self.rank = rank
        self.scale = alpha / rank
        self.lora_a = nn.Parameter(torch.empty(rank, base.in_features, dtype=base.weight.dtype))
        self.lora_b = nn.Parameter(torch.zeros(base.out_features, rank, dtype=base.weight.dtype))
        nn.init.kaiming_uniform_(self.lora_a, a=math.sqrt(5))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.base(x) + (x @ self.lora_a.t() @ self.lora_b.t()) * self.scale


# -- the model ------------------------------------------------------------------

class FreewillVLM(nn.Module):
    def __init__(self, vision: nn.Module, language: nn.Module, tokenizer, spec: dict) -> None:
        super().__init__()
        self.spec = spec
        self.vision = vision
        self.language = language
        self.tokenizer = tokenizer
        vision_width = vision.config.hidden_size
        text_width = language.config.hidden_size
        bridge = spec.get("projector", {})
        self.bridge = Bridge(vision_width, text_width, bridge.get("shuffle", 2), bridge.get("hidden"))
        self.image_size = int(spec.get("image_size", vision.config.image_size))
        self.lora_rank = 0
        self.grown: list[int] = []      # positions of the layers added by growth, in the current stack
        for p in list(self.vision.parameters()) + list(self.language.parameters()):
            p.requires_grad_(False)
        self.bridge.to(next(language.parameters()).dtype)

    # -- sizes ------------------------------------------------------------------

    def layers(self) -> nn.ModuleList:
        return self.language.model.layers

    def count(self) -> dict:
        """The parameters this model computes with, counted from its tensors."""
        def n(module) -> int:
            return sum(p.numel() for p in module.parameters())
        lora = sum(p.numel() for name, p in self.named_parameters() if ".lora_" in name)
        grown = sum(n(self.layers()[i]) for i in self.grown)
        return {"vision": n(self.vision), "bridge": n(self.bridge), "language": n(self.language) - lora - grown,
                "grown_layers": grown, "lora": lora, "total": n(self),
                "layers": len(self.layers()), "grown_count": len(self.grown), "lora_rank": self.lora_rank}

    # -- adapters and growth ----------------------------------------------------

    def add_lora(self, rank: int, alpha: float | None = None, targets: list[str] | None = None) -> None:
        """Low-rank adapters on the layers the model was born with (grown layers are trained whole)."""
        if self.lora_rank:
            raise ValueError("adapters are already in place")
        conf = self.spec.get("lora", {})
        targets = targets or conf.get("targets") or ["q_proj", "v_proj"]
        alpha = alpha or conf.get("alpha") or 2 * rank
        for index, layer in enumerate(self.layers()):
            if index in self.grown:
                continue
            for parent in layer.modules():
                for name, child in list(parent.named_children()):
                    if name in targets and isinstance(child, nn.Linear):
                        setattr(parent, name, LoRALinear(child, rank, alpha))
        self.lora_rank = rank

    def grow(self, count: int = 1) -> list[int]:
        """Add `count` decoder layers, spread through the stack, each a copy of its neighbour whose
        output projections are zero, so that it adds nothing to the residual stream at first.
        Refused if the model would pass the ceiling of spec.json. Returns the new positions."""
        if self.lora_rank:
            raise ValueError("grow before adding adapters")
        ceiling = int(self.spec.get("ceiling_parameters") or 0)
        layers = self.layers()
        per_layer = sum(p.numel() for p in layers[0].parameters())
        if ceiling and self.count()["total"] + count * per_layer > ceiling:
            raise ValueError(f"growing by {count} layer(s) of {per_layer:,} parameters would pass the ceiling of {ceiling:,}")
        added = []
        for k in range(count):
            original = [i for i in range(len(layers)) if i not in self.grown]
            source = original[min(len(original) - 1, (k * 2 + 1) * len(original) // (2 * count))]
            # Place it after the source, and after any layer already grown there.
            at = source + 1
            while at in self.grown:
                at += 1
            layer = copy.deepcopy(layers[source])
            for module in layer.modules():
                for name in ("o_proj", "down_proj"):
                    target = getattr(module, name, None)
                    if isinstance(target, nn.Linear):
                        nn.init.zeros_(target.weight)
                        if target.bias is not None:
                            nn.init.zeros_(target.bias)
            for p in layer.parameters():
                p.requires_grad_(False)
            layers.insert(at, layer)
            self.grown = [i + 1 if i >= at else i for i in self.grown] + [at]
            config = self.language.config
            if isinstance(getattr(config, "layer_types", None), list):
                config.layer_types.insert(at, config.layer_types[source])
            added.append(at)
        self.grown.sort()
        self._renumber()
        return added

    def _renumber(self) -> None:
        layers = self.layers()
        self.language.config.num_hidden_layers = len(layers)
        for index, layer in enumerate(layers):
            attention = getattr(layer, "self_attn", None)
            if attention is not None and hasattr(attention, "layer_idx"):
                attention.layer_idx = index
            if hasattr(layer, "layer_idx"):
                layer.layer_idx = index

    # -- what can be trained ----------------------------------------------------

    def trainable(self, parts: set[str]) -> list[nn.Parameter]:
        """parts: any of "bridge", "lora", "grown". Everything else is frozen."""
        chosen = []
        for name, p in self.named_parameters():
            on = (("bridge" in parts and name.startswith("bridge."))
                  or ("lora" in parts and ".lora_" in name)
                  or ("grown" in parts and self._in_grown(name)))
            p.requires_grad_(on)
            if on:
                chosen.append(p)
        return chosen

    def _in_grown(self, name: str) -> bool:
        prefix = "language.model.layers."
        if not name.startswith(prefix):
            return False
        return int(name[len(prefix):].split(".", 1)[0]) in self.grown

    def own_state(self) -> dict[str, torch.Tensor]:
        """The weights Freewill trained or added: bridge, adapters, grown layers. The rest is the base."""
        return {name: p.detach().clone().contiguous() for name, p in self.named_parameters()
                if name.startswith("bridge.") or ".lora_" in name or self._in_grown(name)}

    def load_own_state(self, state: dict[str, torch.Tensor]) -> None:
        params = dict(self.named_parameters())
        missing = [k for k in state if k not in params]
        if missing:
            raise ValueError(f"weights for parts this model does not have: {missing[:3]}")
        with torch.no_grad():
            for name, tensor in state.items():
                params[name].copy_(tensor.to(params[name].dtype))

    # -- inputs -----------------------------------------------------------------

    @property
    def dtype(self) -> torch.dtype:
        return next(self.language.parameters()).dtype

    def pixels(self, image) -> torch.Tensor:
        """A PIL image → the eye's input: RGB, resized to a square, scaled to [-1, 1]."""
        import numpy as np
        image = image.convert("RGB").resize((self.image_size, self.image_size))
        array = torch.from_numpy(np.asarray(image, dtype="float32") / 255.0).permute(2, 0, 1)
        mean = torch.tensor(IMAGE_MEAN).view(3, 1, 1)
        std = torch.tensor(IMAGE_STD).view(3, 1, 1)
        return ((array - mean) / std).to(self.dtype)

    def see(self, pixels: torch.Tensor) -> torch.Tensor:
        """(N, 3, H, W) → (N, tokens, text_width)."""
        patches = self.vision(pixel_values=pixels.to(self.dtype)).last_hidden_state
        return self.bridge(patches)

    def text_embed(self, ids: list[int]) -> torch.Tensor:
        table = self.language.get_input_embeddings()
        return table(torch.tensor(ids, dtype=torch.long))

    def sequence(self, parts: list, answer: str | None = None, chat: bool = True) -> tuple[torch.Tensor, torch.Tensor]:
        """parts: strings, ("image", PIL image) and ("video", [(seconds, PIL image), ...]).
        Returns (embeddings T×D, labels T), with labels only on the answer's tokens."""
        pieces: list = []          # str | tensor of image tokens
        images = []
        for part in parts:
            if isinstance(part, str):
                pieces.append(part)
            elif part[0] == "image":
                pieces += ["<image>", ("img", len(images)), "</image>"]
                images.append(part[1])
            elif part[0] == "video":
                pieces.append("<video>")
                for seconds, frame in part[1]:
                    pieces += [f" {seconds:.1f}s:", ("img", len(images))]
                    images.append(frame)
                pieces.append("</video>")
            else:
                raise ValueError(f"unknown part {part[0]!r}")
        seen = self.see(torch.stack([self.pixels(i) for i in images])) if images else None

        prefix, suffix = self._chat_frame() if chat else ("", "")
        embeds, labels = [], []

        def add_text(text: str, learn: bool) -> None:
            ids = self.tokenizer.encode(text)
            if ids:
                embeds.append(self.text_embed(ids))
                labels.extend(ids if learn else [-100] * len(ids))

        add_text(prefix, False)
        text_run = ""
        for piece in pieces:
            if isinstance(piece, str):
                text_run += piece
                continue
            add_text(text_run, False)
            text_run = ""
            tokens = seen[piece[1]]
            embeds.append(tokens)
            labels.extend([-100] * tokens.shape[0])
        add_text(text_run + suffix, False)
        if answer is not None:
            add_text(answer, True)
            embeds.append(self.text_embed([self.tokenizer.eos_id]))
            labels.append(self.tokenizer.eos_id)
        return torch.cat(embeds, 0), torch.tensor(labels, dtype=torch.long)

    def _chat_frame(self) -> tuple[str, str]:
        """The text around a user turn, so that training and conversation share one format."""
        if not self.tokenizer.has_chat_template:
            return "User: ", "\nAssistant: "
        marker = "⁣FREEWILL⁣"
        text = self.tokenizer.inner.apply_chat_template(
            [{"role": "user", "content": marker}], tokenize=False, add_generation_prompt=True,
            enable_thinking=False)
        before, after = text.split(marker, 1)
        return before, after

    # -- scoring and speaking ---------------------------------------------------

    def losses(self, batch: list[tuple[torch.Tensor, torch.Tensor]]) -> torch.Tensor:
        """Mean negative log-likelihood per answer token, one value per sequence (nats)."""
        width = max(e.shape[0] for e, _ in batch)
        dim = batch[0][0].shape[1]
        embeds = torch.zeros(len(batch), width, dim, dtype=self.dtype)
        labels = torch.full((len(batch), width), -100, dtype=torch.long)
        mask = torch.zeros(len(batch), width, dtype=torch.long)
        for row, (e, l) in enumerate(batch):
            embeds[row, : e.shape[0]] = e
            labels[row, : l.shape[0]] = l
            mask[row, : e.shape[0]] = 1
        logits = self.language(inputs_embeds=embeds, attention_mask=mask).logits.float()
        logits, labels = logits[:, :-1], labels[:, 1:]
        per_token = nn.functional.cross_entropy(logits.reshape(-1, logits.shape[-1]), labels.reshape(-1),
                                                ignore_index=-100, reduction="none").view(labels.shape)
        counted = (labels != -100).sum(1).clamp(min=1)
        return per_token.sum(1) / counted

    @torch.no_grad()
    def answer(self, parts: list, max_new_tokens: int = 256) -> str:
        embeds, _ = self.sequence(parts)
        ids = self.language.generate(inputs_embeds=embeds.unsqueeze(0),
                                     attention_mask=torch.ones(1, embeds.shape[0], dtype=torch.long),
                                     max_new_tokens=max_new_tokens, do_sample=False,
                                     eos_token_id=self.tokenizer.eos_id, pad_token_id=self.tokenizer.pad_id)
        return self.tokenizer.decode(ids[0].tolist()).strip()


# -- building -------------------------------------------------------------------

def build(base_dir: Path | None = None, spec: dict | None = None, dtype: str = "float32",
          init: str = "pretrained") -> FreewillVLM:
    """Assemble the model from the two downloaded bases in `base_dir` (`language/` and `vision/`,
    each a Transformers folder). init="random" builds the same architecture with random weights:
    the route for training from zero, which needs far more compute than a personal computer has."""
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, SiglipVisionConfig, SiglipVisionModel

    spec = spec or load_spec()
    torch_dtype = getattr(torch, dtype)
    base_dir = Path(base_dir) if base_dir else None
    language_dir, vision_dir = (base_dir / "language", base_dir / "vision") if base_dir else (None, None)
    tokenizer = HFTokenizer(AutoTokenizer.from_pretrained(language_dir or spec["language"]["repo"],
                                                          revision=None if language_dir else spec["language"]["revision"]))
    if init == "random":
        language = AutoModelForCausalLM.from_config(AutoConfig.from_pretrained(language_dir), dtype=torch_dtype)
        vconf = AutoConfig.from_pretrained(vision_dir)
        vision = SiglipVisionModel(getattr(vconf, "vision_config", vconf)).to(torch_dtype)
    else:
        language = AutoModelForCausalLM.from_pretrained(language_dir, dtype=torch_dtype)
        vision = SiglipVisionModel.from_pretrained(vision_dir, dtype=torch_dtype)
    vision.config.image_size = spec.get("image_size", vision.config.image_size)
    model = FreewillVLM(vision, language, tokenizer, spec)
    model.eval()
    return model


def tiny(seed: int = 0, layers: int = 2) -> FreewillVLM:
    """The same architecture at toy size, random weights, byte tokenizer: for tests only."""
    from transformers import Qwen3Config, Qwen3ForCausalLM, SiglipVisionConfig, SiglipVisionModel

    torch.manual_seed(seed)
    tok = ByteTokenizer()
    language = Qwen3ForCausalLM(Qwen3Config(
        vocab_size=tok.vocab_size, hidden_size=64, intermediate_size=128, num_hidden_layers=layers,
        num_attention_heads=4, num_key_value_heads=2, head_dim=16, max_position_embeddings=1024,
        tie_word_embeddings=True))
    vision = SiglipVisionModel(SiglipVisionConfig(hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                                                  num_attention_heads=2, image_size=32, patch_size=8))
    spec = dict(load_spec(), image_size=32, projector={"shuffle": 2, "hidden": 64},
                ceiling_parameters=0, floor_parameters=0)
    model = FreewillVLM(vision, language, tok, spec)
    model.eval()
    return model
