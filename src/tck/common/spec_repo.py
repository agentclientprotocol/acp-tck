"""Locating the local ACP spec checkout, for tests and `scripts/` tooling run from a source
checkout of this repo."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC_REPO_POINTER = REPO_ROOT / ".agents" / "skills" / "check-specification" / ".repo"


def discover_spec_repo() -> Path | None:
    """The local spec checkout: `$ACP_SPEC_REPO`, else the path the `check-specification` skill
    keeps in its gitignored `.repo` file. `None` when neither is set (e.g. in CI)."""
    configured = os.environ.get("ACP_SPEC_REPO")
    if not configured and SPEC_REPO_POINTER.is_file():
        configured = SPEC_REPO_POINTER.read_text().strip()
    return Path(configured) if configured else None
