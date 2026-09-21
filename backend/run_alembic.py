"""Safe Alembic runner.

Inserts the backend directory into sys.path and changes the working
directory to backend before invoking Alembic, so it works from the
project root.

Examples:
    python backend/run_alembic.py current
    python backend/run_alembic.py revision --autogenerate -m "initial schema"
    python backend/run_alembic.py upgrade head
    python backend/run_alembic.py stamp head
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Change working directory to backend so alembic.ini is found.
os.chdir(BACKEND_DIR)

from alembic.config import main as alembic_main  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    alembic_main(argv=sys.argv[1:])
    return 0


if __name__ == "__main__":
    sys.exit(main())