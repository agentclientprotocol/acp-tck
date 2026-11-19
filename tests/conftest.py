"""Shared test helpers.

Tests drive the harness with plain `asyncio.run(...)` rather than the `pytest-asyncio` plugin --
the harness is the only place async code is exercised, so that's enough.
"""

from __future__ import annotations

import sys
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


def parse_shard(value: str) -> tuple[int, int]:
    """Parse `--shard K/N` (1 <= K <= N) into `(K, N)`."""
    try:
        k_text, n_text = value.split("/")
        k, n = int(k_text), int(n_text)
    except ValueError:
        raise pytest.UsageError(f"--shard expects K/N, got {value!r}") from None
    if not 1 <= k <= n:
        raise pytest.UsageError(f"--shard needs 1 <= K <= N, got {value!r}")
    return k, n


def shard_indices(count: int, k: int, n: int) -> list[int]:
    """Indices of the `count` collected items that shard `K/N` keeps: every N-th, round robin, so
    the slow end-to-end tests spread evenly over the shards."""
    return list(range(k - 1, count, n))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--shard",
        metavar="K/N",
        help="run only shard K of N of the collected tests (CI splits the suite over runners)",
    )


def pytest_configure(config: pytest.Config) -> None:
    value = config.getoption("--shard")
    if value is not None:
        parse_shard(value)  # fail fast, in the xdist controller too


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    value = config.getoption("--shard")
    if value is None:
        return
    k, n = parse_shard(value)
    keep = set(shard_indices(len(items), k, n))
    deselected = [item for i, item in enumerate(items) if i not in keep]
    if deselected:
        config.hook.pytest_deselected(items=deselected)
    items[:] = [item for i, item in enumerate(items) if i in keep]
