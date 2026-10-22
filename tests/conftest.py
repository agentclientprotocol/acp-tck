"""Shared test helpers.

Tests drive the harness with plain `asyncio.run(...)` rather than the `pytest-asyncio` plugin --
the harness is the only place async code is exercised, so that's enough.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn

import pytest

from tck.common.harness import AgentLaunch
from tck.common.spec_repo import discover_spec_repo

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "agents" / "v1"
FIXTURES_DIR_V2 = Path(__file__).parent / "fixtures" / "agents" / "v2"

_FIXTURES_DIR_BY_VERSION = {"v1": FIXTURES_DIR, "v2": FIXTURES_DIR_V2}


def agent_launch(script_name: str, *, version: str = "v1", **overrides: object) -> AgentLaunch:
    """Build an `AgentLaunch` for `tests/fixtures/agents/<version>/<script_name>`, run with the
    same interpreter pytest is running under. Defaults to `"v1"`; pass `version="v2"` for a
    `tests/fixtures/agents/v2/<script_name>` fixture."""
    fixtures_dir = _FIXTURES_DIR_BY_VERSION[version]
    kwargs: dict[str, object] = {
        "command": [sys.executable, str(fixtures_dir / script_name)],
        "startup_timeout": 2.0,
        "default_timeout": 2.0,
    }
    kwargs.update(overrides)
    return AgentLaunch(**kwargs)  # type: ignore[arg-type]


def _in_ci() -> bool:
    """GitHub Actions (and most CI systems) set `CI=true`."""
    return os.environ.get("CI", "").lower() in {"1", "true"}


def _spec_unavailable(reason: str) -> NoReturn:
    """Skip locally; fail under CI, where a missing spec checkout means the fetch step broke and
    skipping would silently hide the spec-map checks."""
    if _in_ci():
        pytest.fail(f"{reason} (CI is set, so this fails instead of skipping)", pytrace=False)
    pytest.skip(reason)


def read_spec_doc(repo: Path | None, revision: str, path: str) -> str:
    """Read `path` from `repo` as of `revision` with `git show`. When the checkout or revision is
    missing, skips locally and fails under CI (see `_spec_unavailable`)."""
    if repo is None:
        _spec_unavailable("no spec checkout (set ACP_SPEC_REPO or configure check-specification)")
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{revision}:{path}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        if subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"{revision}^{{commit}}"],
            capture_output=True,
        ).returncode != 0:
            _spec_unavailable(f"spec checkout {repo} does not contain revision {revision}")
        raise AssertionError(f"{path} does not exist at spec revision {revision}: {result.stderr.strip()}")
    return result.stdout


@pytest.fixture(scope="session")
def spec_doc() -> Callable[[str, str], str]:
    """`spec_doc(revision, path)` returns a file from the spec repo as of `revision`, read with
    `git show` so the checkout's working tree and current branch do not matter. Skips the test
    when no spec checkout is available or it lacks `revision`; fails instead under CI."""

    repo = discover_spec_repo()
    return lambda revision, path: read_spec_doc(repo, revision, path)
