"""Paths shared by source and packaged application runs."""

from pathlib import Path
import sys


def application_directory() -> Path:
    """Return the folder containing project runtime files."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = application_directory()
COMPOSE_FILE = PROJECT_ROOT / "compose.yaml"
