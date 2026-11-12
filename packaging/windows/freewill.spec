# PyInstaller recipe for the Windows application.
# Run from the repository root: pyinstaller packaging/windows/freewill.spec
from pathlib import Path

root = Path(SPECPATH).resolve().parents[1]
package = root / "freewill"

datas = [(str(path), "freewill/ui") for path in (package / "ui").iterdir() if path.is_file()]
# The data files the package reads at run time: the catalogue of models, the credits, the pinned runtime
# and the reference texts of engine learning. (Version 1.0 shipped without the first two.)
datas += [(str(package / name), "freewill") for name in ("models.json", "credits.json", "runtime.json")]
# The exact commit this build comes from, written by the workflow (freewill/build.py reads it)
if (package / "build.json").exists():
    datas += [(str(package / "build.json"), "freewill")]
datas += [(str(package / "learning" / "reference.json"), "freewill/learning")]
datas += [(str(package / "learning" / "rehearsal.json"), "freewill/learning")]
# llama.cpp, fetched and checked against runtime.json by the workflow before this recipe runs
# (python -m freewill.runtime --target runtime --platform win-x64). Without it the build stops.
runtime = root / "runtime"
if not (runtime / "llama-server.exe").is_file():
    raise SystemExit("runtime/llama-server.exe is missing: run python -m freewill.runtime --target runtime --platform win-x64")
datas += [(str(path), "runtime") for path in runtime.iterdir() if path.is_file()]
# The kernel's fingerprint is computed over its own source files: ship them as they are.
datas += [(str(path), "freewill/core/kernel") for path in (package / "core" / "kernel").glob("*.py")]

a = Analysis(
    [str(root / "packaging" / "windows" / "launcher.py")],
    pathex=[str(root)],
    datas=datas,
    hiddenimports=["anthropic", "keyring.backends.Windows", "pypdf"],
    excludes=["tkinter", "pytest"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Freewill",
    console=False,
    icon=str(root / "packaging" / "windows" / "freewill.ico"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="Freewill")
