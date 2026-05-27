"""Patch existing Windows EXE files to use resources/icon.ico."""
from __future__ import annotations

import glob
import os

from PyInstaller import config
from PyInstaller.utils.win32.icon import CopyIcons


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON = os.path.join(ROOT, "resources", "icon.ico")


def main() -> None:
    config.CONF["workpath"] = os.path.join(ROOT, "build", "_icon_work")
    os.makedirs(config.CONF["workpath"], exist_ok=True)

    patterns = [
        os.path.join(ROOT, "dist_nuitka", "TongueSeg.dist", "TongueSeg.exe"),
        os.path.join(ROOT, "dist", "TongueSeg", "TongueSeg.exe"),
        os.path.join(ROOT, "installer", "*.exe"),
        os.path.join(ROOT, "installer", "dist", "*.exe"),
    ]

    targets: list[str] = []
    for pattern in patterns:
        targets.extend(glob.glob(pattern))

    for target in sorted(set(targets)):
        try:
            CopyIcons(target, ICON)
            print(f"updated: {target}")
        except Exception as exc:
            print(f"skipped: {target} ({type(exc).__name__}: {exc})")


if __name__ == "__main__":
    main()
