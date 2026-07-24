"""Shared Julia executable detection for ``ps_bhlp`` and ``setup_julia``."""

import shutil
from pathlib import Path


def find_julia() -> str | None:
    """Return the path to the Julia executable, or ``None`` if not found.

    Checks ``julia`` on PATH first, then common Windows install directories.
    """
    found = shutil.which("julia")
    if found:
        return found

    for base in (
        Path.home() / "AppData" / "Local" / "Programs",
        Path("C:/Program Files"),
    ):
        if base.exists():
            for d in sorted(base.glob("Julia-*"), reverse=True):
                exe = d / "bin" / "julia.exe"
                if exe.exists():
                    return str(exe)

    return None