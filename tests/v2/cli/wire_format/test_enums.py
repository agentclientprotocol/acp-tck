"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_enums.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _fails, _full_run, _run_cli, _table_statuses


def test_unprefixed_cursor_anchor_values_fail_only_enum_201(tmp_path):
    """`anchor.type` is `"hologram"` and `anchor.position` `"beside"`: the `other` branches accept
    them, `ACP-CURSOR-001..004` ignore an anchor of unknown `type`, and only the open-enum sweep
    objects."""
    statuses, _by_id, stdout = _full_run("cursor_anchor_custom_type.py", tmp_path)
    assert _fails(statuses) == {"ACP-ENUM-201"}, stdout
    for n in (1, 2, 3, 4):
        assert statuses[f"ACP-CURSOR-00{n}"] in ("PASS", "SKIPPED"), stdout


def test_unprefixed_background_type_fails_only_enum_201(tmp_path):
    """`background[].type` is `"task"`: the `other` branch accepts it, `ACP-STATE-206..208` ignore
    items of other types, and only the open-enum sweep objects."""
    statuses, _by_id, stdout = _full_run("unprefixed_background_type.py", tmp_path)
    assert _fails(statuses) == {"ACP-ENUM-201"}, stdout
    for req_id in ("ACP-STATE-206", "ACP-STATE-207", "ACP-STATE-208"):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{stdout}"


def _enum_201_run(fixture: str):
    return _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_enums")


def test_unprefixed_custom_session_update_fails_enum_201_only():
    """`unprefixed_custom_session_update.py` sends one `session/update` with
    `sessionUpdate: "surprise"` (neither a defined constant nor `_`-prefixed) -- FAILs
    `ACP-ENUM-201` only. The `SessionUpdate` `$def`'s own `"other"`-titled fallback branch only
    requires `sessionUpdate` to be a string, so this does NOT cascade into `ACP-SCHEMA-001`."""
    result = _enum_201_run("unprefixed_custom_session_update.py")
    assert result.returncode != 0
    assert _fails(_table_statuses(result.stdout)) == {"ACP-ENUM-201"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_prefixed_custom_session_update_passes_enum_201():
    """Positive control for the rule above: `_tck_custom_update` is `_`-prefixed, so
    `ACP-ENUM-201` PASSes."""
    result = _enum_201_run("prefixed_custom_session_update.py")
    assert _fails(_table_statuses(result.stdout)) == set(), result.stdout
    assert _table_statuses(result.stdout).get("ACP-ENUM-201") == "PASS", result.stdout


def test_unprefixed_custom_state_fails_enum_201_only():
    """`unprefixed_custom_state.py` sends `state_update{state: "busy"}` mid-turn, then a normal
    idle. The unrecognised state never ends the turn, so the turn still completes (no timeout
    cascade); the full suite FAILs only `ACP-ENUM-201`."""
    result = _run_cli(FIXTURES_DIR_V2, "unprefixed_custom_state.py", protocol_version=2)
    assert result.returncode != 0
    assert _fails(_table_statuses(result.stdout)) == {"ACP-ENUM-201"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_unprefixed_custom_permission_kind_fails_enum_201_only():
    """`unprefixed_custom_permission_kind.py` offers a permission option with `kind: "sorcery"`
    -- schema-valid via `PermissionOptionKind`'s `other` branch, so only `ACP-ENUM-201` FAILs."""
    result = _run_cli(FIXTURES_DIR_V2, "unprefixed_custom_permission_kind.py", protocol_version=2)
    assert result.returncode != 0
    assert _fails(_table_statuses(result.stdout)) == {"ACP-ENUM-201"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_prefixed_custom_permission_kind_passes_enum_201():
    """Positive control: `_tck_custom_kind` is `_`-prefixed, so `ACP-ENUM-201` PASSes -- and
    really checked, since this fixture does ask for permission."""
    result = _enum_201_run("prefixed_custom_permission_kind.py")
    assert _fails(_table_statuses(result.stdout)) == set(), result.stdout
    assert _table_statuses(result.stdout).get("ACP-ENUM-201") == "PASS", result.stdout


def test_unprefixed_chunk_content_type_fails_enum_201_only():
    """`unprefixed_chunk_content_type.py` sends a `tool_call_content_chunk` whose single `content`
    object has `type: "sorcery"`. The chunk's `content` is one object, so this guards the sweep
    reading it as such; the schema's `other` branch accepts it, so only `ACP-ENUM-201` FAILs."""
    result = _enum_201_run("unprefixed_chunk_content_type.py")
    assert result.returncode != 0
    assert _fails(_table_statuses(result.stdout)) == {"ACP-ENUM-201"}, result.stdout


def test_unprefixed_diff_operation_fails_enum_201_only():
    """`unprefixed_diff_operation.py` sends `diff` content with a change `operation` of
    `"teleport"` -- schema-valid via `DiffChange`'s `other` branch, so only `ACP-ENUM-201` FAILs."""
    result = _enum_201_run("unprefixed_diff_operation.py")
    assert result.returncode != 0
    assert _fails(_table_statuses(result.stdout)) == {"ACP-ENUM-201"}, result.stdout


def test_accepts_contentless_embedded_resource_fails_enum_204_only():
    """`accepts_contentless_embedded_resource.py` advertises `embeddedContext` but accepts a
    `resource` block with neither `text` nor `blob`: only the ADVISORY `ACP-ENUM-204` FAILs;
    an ordinary resource block is still accepted (`ACP-PROMPTCAP-003`)."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "accepts_contentless_embedded_resource.py",
        protocol_version=2,
        k="test_enums or prompt_capabilities",
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-ENUM-204"}, result.stdout
    assert statuses.get("ACP-PROMPTCAP-003") == "PASS", result.stdout
