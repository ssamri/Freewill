"""What is thought stays in the Subconscious; the conversation holds only what is said."""

import random

from freewill.core.conscious import Decision, system_prompt
from freewill.core.life import Life
from freewill.core.loop import Being
from freewill.core.speech import separate, strip_reasoning
from freewill.engines.compatible import parse_json_object
from freewill.engines.simulated import SimulatedEngine


# -- the rules -------------------------------------------------------------------

def test_reasoning_blocks_are_set_aside():
    assert strip_reasoning("<think>The person greets me.</think>Hello Sam!") == ("Hello Sam!", "The person greets me.")
    assert strip_reasoning("Hello<thinking>should I ask?</thinking> Sam") == ("Hello Sam", "should I ask?")
    assert strip_reasoning("I am thinking about it.</think>Yes.") == ("Yes.", "I am thinking about it.")
    assert strip_reasoning("Bonjour !<think>il faut répondre") == ("Bonjour !", "il faut répondre")
    assert strip_reasoning("Plain words, no tags.") == ("Plain words, no tags.", "")


def test_a_thought_written_as_speech_stays_inside_when_nobody_spoke():
    thought = "I wonder who made me, and why."
    said, kept, why = separate("I wonder who made me, and why.", thought=thought,
                               content="A question I carry returns: who made me?", spoken_to=False)
    assert said == "" and kept == thought and why == "repeats_thought"

    content = "Out of nowhere, I think of “the sea”."
    said, kept, why = separate("Out of nowhere, I think of the sea.", thought="", content=content, spoken_to=False)
    assert said == "" and "the sea" in kept and why == "repeats_content"

    said, kept, why = separate("(thinking: maybe I should rest)", thought="", content="x", spoken_to=False)
    assert said == "" and "rest" in kept and why == "stage_direction"
    said, kept, why = separate("Pensée : je suis fatiguée.", thought="", content="x", spoken_to=False)
    assert said == "" and why == "stage_direction"


def test_words_addressed_to_the_person_are_left_to_the_conversation():
    # Speaking first is allowed: words that are not the thought written out reach the conversation.
    said, kept, why = separate("Anass, may I ask you something?", thought="I wonder who made me.",
                               content="A question I carry returns: who made me?", spoken_to=False)
    assert said == "Anass, may I ask you something?" and why == ""
    # An answer to the person is an answer, even when it says what it thinks.
    said, kept, why = separate("I am Ada.", thought="I am Ada.", content="Who are you?", spoken_to=True)
    assert said == "I am Ada." and why == ""
    # ... but its reasoning is not part of it.
    said, kept, why = separate("<think>He asks my name.</think>I am Ada.", thought="", content="Who are you?",
                               spoken_to=True)
    assert said == "I am Ada." and kept == "He asks my name." and why == "reasoning"


def test_the_json_of_a_reasoning_model_is_found_after_its_reasoning():
    text = '<think>I should answer {kindly}.</think>\n{"decision": "accept", "say": "Hi"}'
    assert parse_json_object(text) == {"decision": "accept", "say": "Hi"}


def test_tags_do_not_survive_in_the_other_fields():
    decision = Decision.from_engine({"decision": "accept", "reason": "<think>why</think> because",
                                     "thought": "<think>hmm</think>", "say": "", "remember": False,
                                     "memory_title": "", "memory_summary": "", "memory_compartment": "",
                                     "new_value": ""})
    assert "<" not in decision.reason + decision.thought


def test_the_engine_is_told_that_its_thoughts_are_not_heard(tmp_path):
    prompt = system_prompt(Life.birth(tmp_path, "Ada", seed=1))
    assert "the person does not hear them" in prompt and "never write your thought" in prompt


# -- in the life loop ------------------------------------------------------------------

class _Musing(SimulatedEngine):
    """Writes its thought in "say" every time, as small models were seen doing."""

    def decide(self, system, prompt, schema, hint, images=None):
        answer = super().decide(system, prompt, schema, hint)
        if hint["source"] == "message":
            answer.update(decision="accept", thought="Someone greets me.",
                          say="<think>Someone greets me. I should answer.</think>Hello, I am Ada.")
        else:
            answer.update(decision="accept", thought=f"I keep thinking: {hint['text']}", say=f"I keep thinking: {hint['text']}")
        return answer


def test_in_the_loop_thoughts_reach_the_subconscious_and_not_the_conversation(tmp_path):
    life = Life.birth(tmp_path, "Ada", language="en", interlocutor="Sam", seed=3)
    being = Being(life, _Musing(seed=3), rng=random.Random(3))
    events = []
    being.events.subscribe(events.append)
    for _ in range(4):
        being.tick()
    being.hear("Hello!")
    for _ in range(3):
        being.tick()
        if not being.inbox:
            break
    speech = [e.data["text"] for e in events if e.type == "speech"]
    kept = [e for e in events if e.type == "withheld" and e.data.get("what") == "inner_speech"]
    thoughts = [e.data["thought"] for e in events if e.type == "decision"]
    assert speech == ["Hello, I am Ada."]
    assert len(kept) >= 4 and all(k.data["text"] for k in kept)
    assert any("I should answer" in t for t in thoughts)  # nothing is lost: the reasoning joins the thought
    assert [turn["text"] for turn in being.dialogue if turn["who"] == "self"] == ["Hello, I am Ada."]
