"""The stage: a workspace of narrow capacity.

Proposals compete. One prevails and is broadcast to the whole system; the
others stay below the threshold of attention, where they can still be seen
by whoever is observing.
"""

from __future__ import annotations

from dataclasses import dataclass

from freewill.core.subconscious import Proposal


@dataclass
class Competition:
    winner: Proposal
    others: list[Proposal]


def compete(proposals: list[Proposal]) -> Competition | None:
    if not proposals:
        return None
    ranked = sorted(proposals, key=lambda proposal: proposal.salience, reverse=True)
    return Competition(ranked[0], ranked[1:])
