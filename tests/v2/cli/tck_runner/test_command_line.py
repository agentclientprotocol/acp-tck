"""End-to-end tests of `acp-tck` itself: its command line: help, version, argument errors, `-k` scoping and the per-test watchdog."""

from __future__ import annotations

import subprocess
import sys

from .._runner import FIXTURES_DIR_V1, _run_cli


def test_help_mentions_protocol_version_option():
    result = subprocess.run(
        [sys.executable, "-m", "tck", "--help"], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "--protocol-version" in result.stdout


def test_v2_missing_agent_command_is_an_error():
    result = subprocess.run(
        [sys.executable, "-m", "tck", "--protocol-version", "2"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0


def test_default_protocol_version_still_runs_the_v1_suite_unchanged():
    """No `--protocol-version` given at all -- must run the v1 suite, against the v1 conforming
    fixture."""
    result = _run_cli(FIXTURES_DIR_V1, "conforming.py", protocol_version=None)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout
    assert "ACP-INIT-002" in result.stdout, "expected the v1 registry's ids, not v2's"


def test_explicit_protocol_version_1_matches_the_default():
    result = _run_cli(FIXTURES_DIR_V1, "conforming.py", protocol_version=1)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_help_mentions_subagent_prompt_options():
    result = subprocess.run([sys.executable, "-m", "tck", "--help"], capture_output=True, text=True, timeout=10)
    assert "--subagent-prompt" in result.stdout
    assert "--subagent-cancel-prompt" in result.stdout
