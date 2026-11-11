"""The single event stream: everything that happens in the core is emitted here.

It feeds whatever is watching in real time, and it is the complete,
append-only log of the being's life.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Event:
    type: str
    time: str
    data: dict = field(default_factory=dict)


Listener = Callable[[Event], None]


class EventStream:
    def __init__(self, log_path: Path | None = None) -> None:
        self._log_path = log_path
        self._listeners: list[Listener] = []

    def subscribe(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def emit(self, type: str, **data) -> Event:
        event = Event(type, datetime.now(timezone.utc).isoformat(timespec="seconds"), data)
        if self._log_path is not None:
            with self._log_path.open("a", encoding="utf-8") as log:
                log.write(json.dumps({"type": event.type, "time": event.time, **event.data},
                                     ensure_ascii=False) + "\n")
        for listener in self._listeners:
            listener(event)
        return event
