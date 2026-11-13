"""The TCK's own pytest run must not inherit config from an outer project.

The repo's root `pyproject.toml` sets `addopts = ["-n", "auto"]`; pytest finds config by walking
up from the args, and plugin option values (agent command, `--agent-cwd`, ...) that are existing
paths count as args because the plugin has not registered its options yet at that point. So the
run passes the conformance `pytest.ini` with `-c`, and blocks xdist (the report needs one
process). Runs are subprocesses because this file itself runs under pytest. `PYTEST_ADDOPTS` is
dropped from the child's environment except in the test that sets it on purpose.
"""

from __future__ import annotations

import os
import shlex
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
FIXTURES = Path(__file__).parent.parent / "fixtures" / "agents"


def _assert_isolated(output: str, version: str) -> None:
    assert "configfile: pytest.ini" in output, output
    rootdir = next(line for line in output.splitlines() if line.startswith("rootdir: "))
    assert rootdir.replace("\\", "/").endswith(f"/tck/{version}/conformance"), output
    assert "workers" not in output, output
    assert "[gw" not in output, output


def _assert_real_verdict(output: str) -> None:
    assert "no test executed" not in output, output
    assert "VERDICT:" in output, output


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
    _assert_real_verdict(result.stdout)


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_plain_pytest_tck_invocation_is_isolated_too(version: str) -> None:
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
            f"src/tck/{version}/conformance", "-c", f"src/tck/{version}/conformance/pytest.ini",
            "-p", f"tck.{version}.plugin",
            "--tck-agent-cmd", shlex.join([sys.executable, str(FIXTURES / version / "conforming.py")]),
            "--tck-timeout", "2", "--tck-startup-timeout", "2", "-k", "initialize",
        ],
        capture_output=True, text=True, timeout=60, env=_env(),
        cwd=REPO_ROOT,
    )
    _assert_isolated(result.stdout, version)
    _assert_real_verdict(result.stdout)


@pytest.fixture
def repo_wrapper(request: pytest.FixtureRequest) -> Iterator[Path]:
    """An executable wrapper script (running the v1 or v2 conforming fixture) inside the repo, so
    that using it as the whole agent command makes an option value an existing path in the repo."""
    version = request.getfixturevalue("version")
    with tempfile.TemporaryDirectory(prefix="tck-iso-", dir=REPO_ROOT) as tmp:
        wrapper = Path(tmp) / "agent.sh"
        wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FIXTURES / version / "conforming.py"}"\n')
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)
        yield wrapper


@pytest.mark.skipif(sys.platform == "win32", reason="uses a shell-script agent wrapper")
@pytest.mark.parametrize("version", ["v1", "v2"])
def test_agent_command_that_is_a_path_inside_the_repo_does_not_change_config(
    version: str, repo_wrapper: Path
) -> None:
    result = subprocess.run(
        [
            sys.executable, "-m", "tck", "--protocol-version", version[1:],
            "--timeout", "2", "--startup-timeout", "2", "-k", "initialize",
            "--", str(repo_wrapper),
        ],
        capture_output=True, text=True, timeout=60, env=_env(),
    )
    _assert_isolated(result.stdout, version)
    _assert_real_verdict(result.stdout)


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_agent_cwd_inside_the_repo_does_not_change_config(version: str) -> None:
    result = subprocess.run(
        [
            sys.executable, "-m", "tck", "--protocol-version", version[1:],
            "--timeout", "2", "--startup-timeout", "2", "-k", "initialize",
            "--agent-cwd", str(REPO_ROOT / "tests"),
            "--", sys.executable, str(FIXTURES / version / "conforming.py"),
        ],
        capture_output=True, text=True, timeout=60, env=_env(),
    )
    _assert_isolated(result.stdout, version)
    _assert_real_verdict(result.stdout)


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_pytest_addopts_xdist_fails_loudly_instead_of_an_empty_report(version: str) -> None:
    result = subprocess.run(
        [
            sys.executable, "-m", "tck", "--protocol-version", version[1:],
            "--timeout", "2", "--startup-timeout", "2", "-k", "initialize",
            "--", sys.executable, str(FIXTURES / version / "conforming.py"),
        ],
        capture_output=True, text=True, timeout=60, env={**_env(), "PYTEST_ADDOPTS": "-n 2"},
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "unrecognized arguments: -n" in result.stderr, result.stderr
    assert "VERDICT:" not in result.stdout, result.stdout
