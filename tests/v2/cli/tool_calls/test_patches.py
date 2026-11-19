"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_patches.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

from .._runner import FIXTURES_DIR_V2, _TOOL_CALL_K, _fails, _run_cli, _table_statuses


def test_tool_call_update_missing_id_fails_patch_204_and_schema_001():
    """`tool_call_update_missing_id.py` emits one `tool_call_update` with no `toolCallId` --
    FAILs `ACP-PATCH-204` directly, and cascades into `ACP-SCHEMA-001` since `ToolCallUpdate`
    schema-requires `toolCallId` (`schema/v2/schema.unstable.json#/$defs/ToolCallUpdate`). It overrides
    `_send_rich_turn_updates`, which `_base.py` calls on *every* turn, so it also cascades into
    `ACP-PROMPT-002` (CAPABILITY -- schema-validates every `session/update` a driven turn
    observes). Within this `-k`, which includes `test_prompt` for that cascade."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "tool_call_update_missing_id.py",
        protocol_version=2,
        k="test_patches or initialize or (test_prompt and not capabilities)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-PATCH-204", "ACP-SCHEMA-001", "ACP-PROMPT-002"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_plan_missing_plan_id_fails_patch_205_and_schema_001():
    """`plan_missing_plan_id.py` emits one `plan_update` whose `plan` object has no `planId` --
    FAILs `ACP-PATCH-205` directly, and cascades into `ACP-SCHEMA-001` since `PlanItems`
    schema-requires `planId` (`schema/v2/schema.unstable.json#/$defs/PlanItems`). Same
    `_send_rich_turn_updates`-on-every-turn cascade as the sibling test above also FAILs
    `ACP-PROMPT-002` within this `-k`, which includes `test_prompt`."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "plan_missing_plan_id.py",
        protocol_version=2,
        k="test_patches or initialize or (test_prompt and not capabilities)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-PATCH-205", "ACP-SCHEMA-001", "ACP-PROMPT-002"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_relative_markdown_plan_path_fails_plan_003():
    """`relative_markdown_plan_path.py` emits one schema-valid markdown `plan_update` with a
    relative `path` -- FAILs `ACP-PLAN-003` only (`AbsolutePath` is a bare string in the schema),
    while `conforming_full.py` (absolute `path`) PASSes it."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "relative_markdown_plan_path.py",
        protocol_version=2,
        k="test_patches or initialize or (test_prompt and not capabilities)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-PLAN-003"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_message_chunk_missing_message_id_fails_patch_201_and_schema_001():
    """`message_chunk_missing_message_id.py` emits one `agent_message_chunk` with no
    `messageId` -- FAILs `ACP-PATCH-201` directly, and cascades into `ACP-SCHEMA-001` since
    `ContentChunk` schema-requires `messageId` (`schema/v2/schema.unstable.json#/$defs/ContentChunk`).
    Same `_send_rich_turn_updates`-on-every-turn cascade as the two sibling tests above also
    FAILs `ACP-PROMPT-002` within this `-k`, which includes `test_prompt`."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "message_chunk_missing_message_id.py",
        protocol_version=2,
        k="test_patches or initialize or (test_prompt and not capabilities)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-PATCH-201", "ACP-SCHEMA-001", "ACP-PROMPT-002"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_permission_for_background_work_needs_no_requires_action(tmp_path):
    """`asks_permission_for_background_work.py` asks permission for its listed background tool
    call while the session stays `running`/`idle`. That request is not for foreground work, so
    `ACP-PATCH-209` SKIPs instead of FAILing, and the permission rows judge it normally."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "asks_permission_for_background_work.py",
        protocol_version=2,
        k=_TOOL_CALL_K,
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    for req_id in (
        "ACP-PERM-201",
        "ACP-PERM-202",
        "ACP-PERM-203",
        "ACP-PERM-002",
        "ACP-PERM-204",
        "ACP-PATCH-208",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-STATE-206",
        "ACP-STATE-207",
        "ACP-STATE-208",
    ):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{result.stdout}"
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    (patch_209,) = by_id["ACP-PATCH-209"]["tests"]
    assert patch_209["status"] == "SKIPPED"
    assert "background work" in patch_209["message"], patch_209
