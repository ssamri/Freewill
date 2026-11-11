"""The closed list of things a being can do. There is nothing else."""

from __future__ import annotations

from enum import Enum


class Action(str, Enum):
    THINK = "think"              # dwell on a content that reached the stage
    DISMISS = "dismiss"          # let a content go
    SPEAK = "speak"              # say something to the interlocutor
    REMEMBER = "remember"        # write a memory inside its own life file
    ADOPT_VALUE = "adopt_value"  # add a value to its own values
    REST = "rest"                # withdraw for a while
    READ = "read"                # read or look at something the person gave it
    DREAM = "dream"              # recombine its own memories during sleep


# Hard bounds on what an action may carry.
MAX_SPEECH_CHARS = 4000
MAX_MEMORY_CHARS = 8000
MAX_VALUE_CHARS = 300
MAX_DREAM_CHARS = 6000
