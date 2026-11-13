"""The TCK's own pytest run must not inherit config from an outer project.

The repo's root `pyproject.toml` sets `addopts = ["-n", "auto"]`; pytest finds config by walking
up from the args, so without the `pytest.ini` beside each conformance suite the inner run would
pick that up (and, installed, whatever project config surrounds the venv). Runs are subprocesses
because this file itself runs under pytest. `PYTEST_ADDOPTS` is dropped from the child's
environment: it is an explicit operator override that deliberately still applies.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures" / "agents"


def _assert_isolated(output: str, version: str) -> None:
    assert "configfile: pytest.ini" in output, output
    rootdir = next(line for line in output.splitlines() if line.startswith("rootdir: "))
    assert rootdir.replace("\\", "/").endswith(f"/tck/{version}/conformance"), output
    assert "workers" not in output, output
    assert "[gw" not in output, output


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k != "PYTEST_ADDOPTS"}


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_acp_tck_run_uses_conformance_pytest_ini_and_is_not_parallel(version: str) -> None:
    result = subprocess.run(
        [
            sys.executable, "-m", "tck", "--protocol-version", version[1:],
            "--timeout", "2", "--startup-timeout", "2", "-k", "initialize",
            "--", sys.executable, str(FIXTURES / version / "conforming.py"),
        ],
        capture_output=True, text=True, timeout=60, env=_env(),
    )
    _assert_isolated(result.stdout, version)


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_plain_pytest_tck_invocation_is_isolated_too(version: str) -> None:
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
            f"src/tck/{version}/conformance", "-p", f"tck.{version}.plugin",
            "--tck-agent-cmd", shlex.join([sys.executable, str(FIXTURES / version / "conforming.py")]),
            "--tck-timeout", "2", "--tck-startup-timeout", "2", "-k", "initialize",
        ],
        capture_output=True, text=True, timeout=60, env=_env(),
        cwd=Path(__file__).parent.parent.parent,
    )
    _assert_isolated(result.stdout, version)
