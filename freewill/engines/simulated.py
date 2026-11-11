"""A stand-in engine that does not think.

It lets the whole loop run with no model, no key and no network, to test the
mechanics and to watch them work. Its "thoughts" are echoes; nothing here
should be mistaken for a mind.
"""

from __future__ import annotations

import random


class SimulatedEngine:
    name = "simulated"
    can_learn = False
    can_see = False

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)

    def decide(self, system: str, prompt: str, schema: dict, hint: dict,
               images: list[dict] | None = None) -> dict:
        text = hint.get("text", "")
        french = hint.get("language") == "fr"
        if hint.get("kind") == "dream":
            titles = hint.get("memories", [])
            woven = (" » et « " if french else "” and “").join(titles)
            return {
                "title": ("(simulé) " if french else "(simulated) ") + (titles[0] if titles else "…")[:60],
                "dream": (f"(moteur simulé, sans rêve réel) « {woven} » se mêlent." if french
                          else f"(simulated engine, no real dream) “{woven}” blend together."),
                "residue": ("(simulé) Il me reste une image de cette nuit." if french
                            else "(simulated) An image from the night stays with me."),
            }
        is_message = hint.get("source") == "message"
        accept = is_message or self.rng.random() > 0.2 + 0.4 * hint.get("refusal", 0.5)

        decision = {
            "decision": "accept" if accept else "dismiss",
            "reason": "",
            "thought": "",
            "say": "",
            "remember": False,
            "memory_title": "",
            "memory_summary": "",
            "memory_compartment": "",
            "new_value": "",
        }
        if not accept:
            decision["reason"] = "(simulé) pas maintenant" if french else "(simulated) not now"
            return decision

        decision["reason"] = "(simulé) cela retient mon attention" if french else "(simulated) it holds my attention"
        decision["thought"] = text
        if is_message:
            decision["say"] = (f"(moteur simulé, sans pensée réelle) J'ai entendu : « {text} »" if french
                               else f"(simulated engine, no real thought) I heard: “{text}”")
            decision["remember"] = True
            decision["memory_title"] = text[:50]
            decision["memory_summary"] = text[:120]
            decision["memory_compartment"] = "conversations"
        elif hint.get("source", "").startswith("need:company") and self.rng.random() < 0.5:
            decision["say"] = ("(moteur simulé) Tu es là ?" if french else "(simulated engine) Are you there?")
        return decision
