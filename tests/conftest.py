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

import pytest

from tck.common.harness import AgentLaunch

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


_SPEC_REPO_POINTER = (
    Path(__file__).resolve().parents[1] / ".agents" / "skills" / "check-specification" / ".repo"
)


def _spec_repo() -> Path | None:
    """The local spec checkout: `$ACP_SPEC_REPO`, else the path the `check-specification` skill
    keeps in its gitignored `.repo` file. `None` when neither is set (e.g. in CI)."""
    configured = os.environ.get("ACP_SPEC_REPO")
    if not configured and _SPEC_REPO_POINTER.is_file():
        configured = _SPEC_REPO_POINTER.read_text().strip()
    return Path(configured) if configured else None


@pytest.fixture(scope="session")
def spec_doc() -> Callable[[str, str], str]:
    """`spec_doc(revision, path)` returns a file from the spec repo as of `revision`, read with
    `git show` so the checkout's working tree and current branch do not matter. Skips the test
    when no spec checkout is available or it lacks `revision`."""

    repo = _spec_repo()

    def read(revision: str, path: str) -> str:
        if repo is None:
            pytest.skip("no spec checkout (set ACP_SPEC_REPO or configure check-specification)")
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
                pytest.skip(f"spec checkout {repo} does not contain revision {revision}")
            raise AssertionError(f"{path} does not exist at spec revision {revision}: {result.stderr.strip()}")
        return result.stdout

    return read
