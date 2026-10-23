"""Declares `--spec-repo` here, at the project root, so pytest registers it before it parses the
command line, even when run from `spec-tracker/` with no test path."""

from __future__ import annotations

from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--spec-repo",
        type=Path,
        default=None,
        help="local clone of the ACP spec repo, for the spec-doc checks (they skip without it)",
    )
