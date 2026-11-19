"""End-to-end tests of `acp-tck` itself: its command line: help, version, argument errors, `-k` scoping and the per-test watchdog."""

from __future__ import annotations

import subprocess
import sys

from .._runner import _run_cli, _table_statuses


def test_help_works():
    result = subprocess.run(
        [sys.executable, "-m", "tck", "--help"], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "acp-tck" in result.stdout


def test_version_works():
    result = subprocess.run(
        [sys.executable, "-m", "tck", "--version"], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "acp-tck" in result.stdout


def test_missing_agent_command_is_an_error():
    result = subprocess.run(
        [sys.executable, "-m", "tck"], capture_output=True, text=True, timeout=10
    )
    assert result.returncode != 0


def test_scoped_k_run_prints_deselection_hint_not_no_mandatory_passed_hint():
    """The `-k`/deselection hint must print whenever any requirement is NOT_TESTED because its
    tests were deselected, independent of whether any MANDATORY
    requirement PASSed -- `conforming.py -k initialize` PASSes several MANDATORY requirements
    (ACP-INIT-*, ACP-TRANSPORT-*, ...) yet is still NOT CONFORMANT overall (every other
    MANDATORY id is NOT_TESTED, which counts as a failure), so this exercises the scoped-run
    branch, not the older "no MANDATORY requirement passed at all" branch, and checks the
    wording distinguishes deselection from an agent that never started."""
    result = _run_cli("conforming.py", k="initialize")
    assert result.returncode != 0
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
    assert "NOT TESTED" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-INIT-001") == "PASS", result.stdout

    assert "hint: this run was scoped" in result.stdout, result.stdout
    assert "-k 'initialize'" in result.stdout, result.stdout
    assert "no MANDATORY requirement passed" not in result.stdout, result.stdout


def test_per_test_watchdog_fails_a_hung_test_fast():
    """A tiny `--test-timeout` must fail a test whose own per-operation deadlines are much
    larger, well before any individual read/write deadline would ever fire on its own --
    proving the watchdog itself is what caught it, not the ordinary per-response timeout.
    Scoped to one fast, id-echo-only test node so this stays quick even though
    `--timeout`/`--startup-timeout` are deliberately large. `--close-grace` is also lowered:
    `never_responds.py` never exits on its own, so teardown would otherwise pay the full
    default 2s stdin-close wait every run just to prove the watchdog fired; this self-test only
    cares that it fired, not about giving a real agent a generous shutdown window."""
    result = _run_cli(
        "never_responds.py",
        k="test_id_is_echoed_for_integer_and_string_ids",
        timeout="10",
        startup_timeout="1",
        test_timeout="0.3",
        close_grace="0.2",
    )
    assert result.returncode != 0
    assert "per-test watchdog" in result.stdout, result.stdout + result.stderr
    assert "--tck-test-timeout" in result.stdout, result.stdout + result.stderr


def test_help_mentions_subagent_prompt_options():
    result = subprocess.run([sys.executable, "-m", "tck", "--help"], capture_output=True, text=True, timeout=10)
    assert "--subagent-prompt" in result.stdout
    assert "--subagent-cancel-prompt" in result.stdout
