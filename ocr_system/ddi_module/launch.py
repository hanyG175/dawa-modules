from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_FILE = BASE_DIR / "app.py"


def main() -> None:
    os.chdir(BASE_DIR)
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
    runpy.run_path(str(APP_FILE), run_name="__main__")


if __name__ == "__main__":
    main()
