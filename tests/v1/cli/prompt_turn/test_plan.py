"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_plan.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_relative_plan_markdown_path_fails_plan_003_only():
    """`emits_relative_plan_markdown_path.py` sends a markdown plan with a relative `path`, only to
    a client that advertised `plan` -- so ACP-CLIENTCAP-006's `plan`-less connection stays clean."""
    result = _run_cli("emits_relative_plan_markdown_path.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-PLAN-003"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-CLIENTCAP-006") == "PASS", result.stdout


def test_file_plan_fails_plan_004_only():
    """`emits_file_plan.py` sends a legacy `file` plan, which no longer validates against the
    schema: ACP-PLAN-004 FAILs and ACP-PLAN-003 (markdown paths only) stays PASS."""
    result = _run_cli("emits_file_plan.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-PLAN-004"}, result.stdout
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-PLAN-003") == "PASS", result.stdout
    assert statuses.get("ACP-CLIENTCAP-006") == "PASS", result.stdout


def test_plan_turn_outlasting_the_timeout_is_judged_on_the_updates_seen():
    """`plan_turn_never_ends.py` sends a valid markdown plan and never resolves the prompt: the
    turn timeout is cancelled and judged on what arrived, so ACP-PLAN-002/003/004 PASS instead of
    FAILing."""
    result = _run_cli("plan_turn_never_ends.py", k="plan")
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-PLAN-002", "ACP-PLAN-003", "ACP-PLAN-004"):
        assert statuses.get(req_id) == "PASS", result.stdout
    assert _output_fail_ids(result.stdout) == set(), result.stdout


def test_plan_despite_plan_capability_fails_plan_002_advisory_only():
    """`sends_plan_despite_plan_capability.py` keeps sending the baseline `plan` update to a client
    that advertised `plan` -- an ADVISORY FAIL, so the run stays CONFORMANT."""
    result = _run_cli("sends_plan_despite_plan_capability.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout
    assert _output_fail_ids(result.stdout) == {"ACP-PLAN-002"}, result.stdout
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-PLAN-003") == "PASS", result.stdout
    assert statuses.get("ACP-PLAN-004") == "PASS", result.stdout
    assert statuses.get("ACP-CLIENTCAP-006") == "PASS", result.stdout
