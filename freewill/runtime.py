"""The program that runs embedded models: llama.cpp, fetched, checked and kept by the application.

Nobody has to install it by hand. The Windows installer carries it. Elsewhere,
or if it is missing, the application fetches the build pinned in
`runtime.json` from llama.cpp's own releases, checks its size and SHA-256, and
keeps only the programs it needs in its data folder. Nothing that does not
match the pin is ever run.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import shutil
import stat
import sys
import tarfile
import threading
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

PIN_PATH = Path(__file__).resolve().parent / "runtime.json"
PROGRAMS = ("llama-server", "llama-perplexity")
_CHUNK = 1 << 20


class RuntimeFetchError(Exception):
    pass


def pin() -> dict:
    return json.loads(PIN_PATH.read_text(encoding="utf-8"))


def platform_key() -> str:
    machine = platform.machine().lower()
    arch = "arm64" if machine in ("arm64", "aarch64") else "x64" if machine in ("x86_64", "amd64") else machine
    system = "win" if sys.platform == "win32" else "macos" if sys.platform == "darwin" else "linux"
    return f"{system}-{arch}"


def exe(name: str) -> str:
    return name + ".exe" if sys.platform == "win32" else name


def installed_dir(data: Path | None = None) -> Path:
    from freewill.paths import data_dir
    return Path(data or data_dir()) / "runtime" / pin()["tag"]


def _candidates(name: str, data: Path | None = None) -> list[Path]:
    named = os.environ.get("FREEWILL_LLAMA_DIR")
    out = [Path(named) / exe(name)] if named else []
    if name == "llama-server" and os.environ.get("FREEWILL_LLAMA_SERVER"):
        out.insert(0, Path(os.environ["FREEWILL_LLAMA_SERVER"]))
    if getattr(sys, "frozen", False):
        out += [Path(getattr(sys, "_MEIPASS", "")) / "runtime" / exe(name),
                Path(sys.executable).parent / "runtime" / exe(name)]
    out.append(Path(__file__).resolve().parents[1] / "runtime" / exe(name))
    out.append(installed_dir(data) / exe(name))
    return out


def find(name: str = "llama-server", data: Path | None = None) -> Path | None:
    """A program of the runtime: bundled, named by FREEWILL_LLAMA_DIR, fetched earlier, or on the PATH."""
    for candidate in _candidates(name, data):
        if candidate.is_file():
            return candidate
    found = shutil.which(name)
    return Path(found) if found else None


def describe(data: Path | None = None) -> dict:
    server = find("llama-server", data)
    asset = pin()["assets"].get(platform_key())
    return {"present": server is not None, "path": str(server) if server else None,
            "perplexity": find("llama-perplexity", data) is not None, "tag": pin()["tag"],
            "platform": platform_key(), "can_fetch": asset is not None,
            "source": pin()["source"], "licence": pin()["licence"]}


class Installer:
    """Fetches the pinned build for this platform once, in the background, and reports progress."""

    def __init__(self, data: Path | None = None) -> None:
        self.data = data
        self.progress: dict = {"state": "idle", "done": 0, "total": 0, "error": None}
        self._lock = threading.Lock()

    def start(self) -> dict:
        with self._lock:
            if self.progress["state"] in ("downloading", "verifying", "unpacking") or find("llama-server", self.data):
                return self.progress
            self.progress = {"state": "downloading", "done": 0, "total": 0, "error": None}
        threading.Thread(target=self._run, daemon=True, name="freewill-runtime").start()
        return self.progress

    def _run(self) -> None:
        try:
            install(self.data, self.progress)
            self.progress["state"] = "done"
        except Exception as error:  # never take the application down
            self.progress.update(state="error", error=f"{type(error).__name__}: {error}")


def install(data: Path | None = None, progress: dict | None = None, *, target: Path | None = None,
            key: str | None = None) -> Path:
    """Fetch, check and unpack the pinned build. Returns the folder that holds the programs.

    `target` and `key` let the build of the Windows installer fetch the Windows build into its own tree."""
    progress = progress if progress is not None else {}
    spec = pin()
    asset = spec["assets"].get(key or platform_key())
    if asset is None:
        raise RuntimeFetchError(f"no pinned llama.cpp build for {key or platform_key()}; "
                            "set FREEWILL_LLAMA_DIR to a folder holding llama-server")
    url = f"{spec['source']}/releases/download/{spec['tag']}/{asset['name']}"
    request = urllib.request.Request(url, headers={"User-Agent": "Freewill"})
    progress.update(total=asset["size"], done=0)
    buffer = io.BytesIO()
    sha = hashlib.sha256()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            while True:
                chunk = response.read(_CHUNK)
                if not chunk:
                    break
                buffer.write(chunk)
                sha.update(chunk)
                progress["done"] = buffer.tell()
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        raise RuntimeFetchError(f"the runtime could not be downloaded: {error}") from error
    progress["state"] = "verifying"
    if buffer.tell() != asset["size"] or sha.hexdigest() != asset["sha256"]:
        raise RuntimeFetchError("the archive received is not the pinned one; it was discarded")
    progress["state"] = "unpacking"
    folder = Path(target) if target else installed_dir(data)
    partial = folder.with_name(folder.name + ".part")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    buffer.seek(0)
    _unpack(buffer, asset["name"], partial, windows=(key or platform_key()).startswith("win"))
    if not (partial / ("llama-server.exe" if (key or platform_key()).startswith("win") else "llama-server")).is_file():
        raise RuntimeFetchError("the archive does not hold llama-server")
    (partial / "freewill_runtime.json").write_text(json.dumps(
        {"tag": spec["tag"], "asset": asset["name"], "sha256": asset["sha256"]}, indent=1) + "\n", encoding="utf-8")
    shutil.rmtree(folder, ignore_errors=True)
    partial.replace(folder)
    return folder


def _wanted(name: str, windows: bool) -> bool:
    """The programs Freewill runs and the libraries they load; nothing else is kept."""
    base = name.rsplit("/", 1)[-1]
    if not base or base.startswith("."):
        return False
    if base in [p + (".exe" if windows else "") for p in PROGRAMS]:
        return True
    return base.endswith((".dll", ".so", ".dylib", ".metal")) or ".so." in base or base.startswith("LICENSE")


def _unpack(buffer: io.BytesIO, name: str, folder: Path, *, windows: bool) -> None:
    def safe(member_name: str) -> str | None:
        base = member_name.replace("\\", "/").rsplit("/", 1)[-1]
        return base if _wanted(member_name.replace("\\", "/"), windows) else None

    if name.endswith(".zip"):
        with zipfile.ZipFile(buffer) as archive:
            for info in archive.infolist():
                base = safe(info.filename)
                if base and not info.is_dir():
                    (folder / base).write_bytes(archive.read(info))
    else:
        with tarfile.open(fileobj=buffer, mode="r:*") as archive:
            links = []
            for member in archive.getmembers():
                base = safe(member.name)
                if not base:
                    continue
                if member.issym() or member.islnk():
                    links.append((base, member.linkname.rsplit("/", 1)[-1]))
                elif member.isfile():
                    (folder / base).write_bytes(archive.extractfile(member).read())
            for base, points_to in links:  # versioned shared libraries: copy, never follow a path out
                if (folder / points_to).is_file() and not (folder / base).exists():
                    shutil.copyfile(folder / points_to, folder / base)
    if not windows:
        for path in folder.iterdir():
            path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IRUSR)


def main(argv: list[str] | None = None) -> int:
    """python -m freewill.runtime [--target DIR] [--platform win-x64]: fetch the pinned build."""
    import argparse
    parser = argparse.ArgumentParser(prog="python -m freewill.runtime")
    parser.add_argument("--target")
    parser.add_argument("--platform")
    args = parser.parse_args(argv)
    folder = install(target=Path(args.target) if args.target else None, key=args.platform)
    print(f"llama.cpp {pin()['tag']} in {folder}: {sorted(p.name for p in folder.iterdir())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
