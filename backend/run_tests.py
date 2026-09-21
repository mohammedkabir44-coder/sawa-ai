"""Safe test runner: inserts backend dir into sys.path, runs pytest programmatically."""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main([
        str(BACKEND_DIR / "tests"),
        str(BACKEND_DIR / "app" / "tests"),
        "-v",
    ]))
