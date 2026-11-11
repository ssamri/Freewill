"""Where Freewill keeps what belongs to the person: lives, models, consent."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return base / "Freewill"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Freewill"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "freewill"
