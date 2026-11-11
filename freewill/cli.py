"""Command line: bring a being into the world, and live alongside it."""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
from pathlib import Path

from freewill import __version__
from freewill.core.affect import AffectSystem
from freewill.core.events import Event
from freewill.core.life import Life
from freewill.core.loop import Being
from freewill.engines.base import EngineError, make_engine

ENGINES = ("simulated", "anthropic", "openai", "xai", "local", "compatible")

_L = {
    "en": {
        "born": "{name} is born. Temperament drawn by lot:",
        "life_at": "Life file: {path}",
        "next": "To live alongside {name}:  python -m freewill live \"{path}\"",
        "awake": "{name} is awake (engine: {engine}). Type to speak. /state, /memory, /quit.",
        "stage": "on stage", "below": "below", "accepted": "welcomed", "dismissed": "let go",
        "recall": "recalls", "remember": "keeps a memory", "value": "adopts a value",
        "silence": "chooses to stay silent", "rest": "rests ({faded} memories faded)",
        "milestone": "first time", "budget": "(thinking paused: hourly budget reached)",
        "error": "engine error", "bye": "{name} goes quiet. Its life is saved.",
        "kernel": "the kernel refused",
    },
    "fr": {
        "born": "Naissance de {name}. Tempérament tiré au sort :",
        "life_at": "Fichier de vie : {path}",
        "next": "Pour vivre à ses côtés :  python -m freewill live \"{path}\"",
        "awake": "{name} s'éveille (moteur : {engine}). Écrivez pour lui parler. /state, /memory, /quit.",
        "stage": "sur scène", "below": "en dessous", "accepted": "accueilli", "dismissed": "écarté",
        "recall": "se rappelle", "remember": "garde un souvenir", "value": "adopte une valeur",
        "silence": "choisit de se taire", "rest": "se repose ({faded} souvenirs estompés)",
        "milestone": "première fois", "budget": "(pensée en pause : budget horaire atteint)",
        "error": "erreur du moteur", "bye": "{name} s'endort. Sa vie est sauvegardée.",
        "kernel": "le noyau a refusé",
    },
}

DIM, BOLD, RESET = "\033[2m", "\033[1m", "\033[0m"


def _labels(language: str) -> dict:
    return _L.get(language, _L["en"])


class Console:
    """Renders the event stream: the being's speech, and its inner life in dim text."""

    def __init__(self, name: str, language: str, *, quiet: bool, color: bool) -> None:
        self.name, self.t, self.quiet = name, _labels(language), quiet
        self.dim, self.bold, self.reset = (DIM, BOLD, RESET) if color else ("", "", "")

    def inner(self, text: str) -> None:
        if not self.quiet:
            print(f"{self.dim}  · {text}{self.reset}", flush=True)

    def __call__(self, event: Event) -> None:
        d, t = event.data, self.t
        if event.type == "speech":
            print(f"{self.bold}{self.name}:{self.reset} {d['text']}", flush=True)
        elif event.type == "stage":
            for other in d["below"][:3]:
                self.inner(f"{t['below']} [{other['source']} {other['salience']:.2f}] {other['text']}")
            self.inner(f"{t['stage']} [{d['source']} {d['salience']:.2f}] {d['text']}")
        elif event.type == "decision":
            verdict = t["accepted"] if d["accepted"] else t["dismissed"]
            self.inner(f"{verdict}: {d['reason']}")
            if d["thought"]:
                self.inner(f"« {d['thought']} »")
        elif event.type == "recall":
            self.inner(f"{t['recall']} ({d['path']}): {d['title']}")
        elif event.type == "remember":
            self.inner(f"{t['remember']}: {d['title']}")
        elif event.type == "value":
            self.inner(f"{t['value']}: {d['text']}")
        elif event.type == "silence":
            self.inner(t["silence"])
        elif event.type == "rest":
            self.inner(t["rest"].format(faded=d["faded"]))
        elif event.type == "milestone":
            self.inner(f"★ {t['milestone']}: {d['name']}")
        elif event.type == "kernel_refusal":
            self.inner(f"{t['kernel']}: {d['message']}")
        elif event.type == "affect_transition":  # H7: a computed state, shown as numbers
            after = d["after"]
            self.inner(f"affect ({d['cause']}): valence {after['valence']:+.2f}, arousal {after['arousal']:.2f}, "
                       f"uncertainty {after['uncertainty']:.2f}")
        elif event.type in ("engine_error", "engine_refusal"):
            print(f"{self.dim}  ! {t['error']}: {d['message']}{self.reset}", flush=True)


def cmd_birth(args: argparse.Namespace) -> int:
    engine = {"kind": args.engine}
    if args.model:
        engine["model"] = args.model
    if args.base_url:
        engine["base_url"] = args.base_url
    try:
        make_engine(engine)  # fail now, not at the first thought
    except EngineError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    try:
        life = Life.birth(Path(args.dir), args.name, language=args.language, engine=engine,
                          interlocutor=args.interlocutor, seed=args.seed, affect=args.affect)
    except FileExistsError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    t = _labels(args.language)
    print(t["born"].format(name=life.name))
    for trait, value in life.genome.to_dict().items():
        if trait != "seed":
            print(f"  {trait}: {value}")
    print(t["life_at"].format(path=life.path))
    print(t["next"].format(name=life.name, path=life.path))
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    life = Life(Path(args.path))
    print(f"{life.name}, {life.age()}  (engine: {life.identity['engine'].get('kind')})")
    print("genome:", {k: v for k, v in life.genome.to_dict().items() if k != "seed"})
    print("needs:", life.state.get("needs"))
    print("thoughts:", life.state.get("thoughts", 0))
    print("values:", [value["text"] for value in life.values] or "none yet")
    print("milestones:", life.milestones or "none yet")
    print("memory:", life.memory.map() or "empty")
    affect = AffectSystem.load(life.path, life.genome.seed)
    print("affect (H7, computed state, not a feeling):",
          affect.state.vector() if affect.enabled else "off")
    return 0


def cmd_affect(args: argparse.Namespace) -> int:
    """Show the computed affective state of a life that is not awake, or switch the mode."""
    life = Life(Path(args.path))
    affect = AffectSystem.load(life.path, life.genome.seed)
    if args.switch:
        affect.set_enabled(args.switch == "on")
    data = affect.public()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    print(f"{life.name}: H7 research mode {'on' if affect.enabled else 'off'} (rules {data['rules']})")
    print("These are computed regulation variables. They are not evidence that anything is felt.")
    if affect.enabled or data["exists"]:
        for name, value in data["state"]["values"].items():
            print(f"  {name:16} {value:+.3f}   rests at {data['setpoints'][name]:+.3f}")
        for item in data["associations"]:
            print(f"  learned  {item['key']:28} {item['valence']:+.3f}  ({item['n']} episodes)")
    return 0


def _read_stdin(lines: "queue.Queue[str | None]") -> None:
    for line in sys.stdin:
        lines.put(line.rstrip("\n"))
    lines.put(None)


def cmd_live(args: argparse.Namespace) -> int:
    life = Life(Path(args.path))
    try:
        engine = make_engine(life.identity.get("engine", {}))
    except EngineError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    t = _labels(life.language)
    being = Being(life, engine)
    being.events.subscribe(Console(life.name, life.language, quiet=args.quiet,
                                   color=sys.stdout.isatty()))
    print(t["awake"].format(name=life.name, engine=engine.name), flush=True)

    lines: "queue.Queue[str | None]" = queue.Queue()
    threading.Thread(target=_read_stdin, args=(lines,), daemon=True).start()

    thought_times: list[float] = []
    next_thought = time.monotonic()
    backoff = 0.0
    warned_budget = False
    lived = 0
    try:
        while True:
            # Listen until it is time for the next thought.
            try:
                line = lines.get(timeout=max(0.05, min(0.5, next_thought - time.monotonic())))
            except queue.Empty:
                line = ""
            if line is None or line.strip() == "/quit":
                break
            if line.strip() == "/state":
                print(f"  needs: {being.needs.to_dict()}  thoughts: {life.state.get('thoughts', 0)}")
                continue
            if line.strip() == "/memory":
                print(f"  memory: {life.memory.map() or 'empty'}")
                continue
            if line.strip():
                being.hear(line)
                next_thought = min(next_thought, time.monotonic() + backoff)

            now = time.monotonic()
            if now < next_thought:
                continue
            # Hourly budget: spontaneous thinking pauses; being spoken to still gets through.
            thought_times = [stamp for stamp in thought_times if now - stamp < 3600]
            if len(thought_times) >= args.thoughts_per_hour and not being.inbox:
                if not warned_budget:
                    print(f"  {t['budget']}", flush=True)
                    warned_budget = True
                next_thought = now + 5
                continue
            warned_budget = False
            try:
                if being.tick() is not None:
                    thought_times.append(now)
                backoff = 0.0
            except EngineError as error:
                if not error.retryable:
                    return 1
                backoff = min(300.0, max(10.0, backoff * 2))
            next_thought = time.monotonic() + args.tempo + backoff
            lived += 1
            if args.moments and lived >= args.moments:
                break
    except KeyboardInterrupt:
        pass
    print(t["bye"].format(name=life.name))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="freewill", description=__doc__)
    parser.add_argument("--version", action="version", version=f"freewill {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    birth = commands.add_parser("birth", help="bring a new being into the world")
    birth.add_argument("name")
    birth.add_argument("--engine", choices=ENGINES, default="simulated",
                       help="which model thinks (default: simulated, which does not really think)")
    birth.add_argument("--model", help="model name; required for openai, xai, local and compatible")
    birth.add_argument("--base-url", help="endpoint for a compatible service")
    birth.add_argument("--language", default="en", choices=("en", "fr"))
    birth.add_argument("--interlocutor", help="your name, as the being will know you")
    birth.add_argument("--dir", default=".", help="where to create the life file")
    birth.add_argument("--seed", type=int, help="fix the genome (for experiments)")
    birth.add_argument("--affect", action="store_true",
                       help="switch on the H7 research mode (computed affective state); off by default")
    birth.set_defaults(run=cmd_birth)

    live = commands.add_parser("live", help="wake a being and stay with it")
    live.add_argument("path", help="path to a .life folder")
    live.add_argument("--tempo", type=float, default=20.0, help="seconds between thoughts")
    live.add_argument("--thoughts-per-hour", type=int, default=120,
                      help="cap on spontaneous thoughts, to bound cost")
    live.add_argument("--quiet", action="store_true", help="show speech only, not the inner life")
    live.add_argument("--moments", type=int, default=0, help="stop after this many moments")
    live.set_defaults(run=cmd_live)

    inspect = commands.add_parser("inspect", help="look at a life file without waking it")
    inspect.add_argument("path")
    inspect.set_defaults(run=cmd_inspect)

    affect = commands.add_parser("affect", help="show or switch the H7 computed affective state of a life")
    affect.add_argument("path")
    affect.add_argument("--on", dest="switch", action="store_const", const="on")
    affect.add_argument("--off", dest="switch", action="store_const", const="off")
    affect.add_argument("--json", action="store_true")
    affect.set_defaults(run=cmd_affect)

    args = parser.parse_args(argv)
    return args.run(args)
