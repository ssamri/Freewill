# PyInstaller recipe for the Windows application.
# Run from the repository root: pyinstaller packaging/windows/freewill.spec
from pathlib import Path

root = Path(SPECPATH).resolve().parents[1]
package = root / "freewill"

datas = [(str(path), "freewill/ui") for path in (package / "ui").iterdir() if path.is_file()]
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
