"""Unit tests for the `ACP-ENUM-201` sweep (`tck.v2.open_enums`) and the `_meta` helpers behind
`ACP-META-203`/`ACP-META-204` (`tck.v2.protocol`), without spawning an agent."""

from __future__ import annotations

import pytest

from tck.v2.open_enums import OpenEnumScan
from tck.v2.protocol import is_namespaced_meta_key, is_valid_traceparent, judge_w3c_meta


def _scan_update(update: dict) -> OpenEnumScan:
    scan = OpenEnumScan()
    scan.scan_update(update)
    return scan


def _diff_item(**overrides) -> dict:
    item = {
        "type": "diff",
        "changes": [{"operation": "modify", "path": "/tmp/a", "fileType": "text"}],
        "patch": {"format": "git_patch", "text": "x"},
    }
    item.update(overrides)
    return item


def test_conforming_values_at_every_site_pass():
    updates = [
        {"sessionUpdate": "state_update", "state": "running"},
        {"sessionUpdate": "tool_call_update", "toolCallId": "t", "kind": "read", "status": "paused",
         "content": [{"type": "session"}, _diff_item()]},
        {"sessionUpdate": "tool_call_content_chunk", "toolCallId": "t", "content": _diff_item()},
        {"sessionUpdate": "plan_update", "plan": {"type": "items", "planId": "p", "entries": [
            {"content": "c", "priority": "high", "status": "pending"}]}},
        {"sessionUpdate": "available_commands_update",
         "availableCommands": [{"type": "command", "name": "n", "description": "d"}]},
    ]
    scan = OpenEnumScan()
    for update in updates:
        scan.scan_update(update)
    assert scan.violations == []
    assert scan.checked > 15


def test_underscore_prefixed_values_pass_everywhere():
    update = {
        "sessionUpdate": "tool_call_update",
        "toolCallId": "t",
        "kind": "_tck_kind",
        "status": "_tck_status",
        "content": [{"type": "_tck_type"}, _diff_item(
            changes=[{"operation": "_tck_op", "path": "/a", "fileType": "_tck_ft"}],
            patch={"format": "_tck_fmt", "text": "x"})],
    }
    assert _scan_update(update).violations == []


@pytest.mark.parametrize(
    ("update", "label"),
    [
        ({"sessionUpdate": "tool_call_update", "toolCallId": "t", "kind": "sorcery"}, "kind"),
        ({"sessionUpdate": "tool_call_update", "toolCallId": "t", "status": "sorcery"}, "status"),
        ({"sessionUpdate": "tool_call_update", "toolCallId": "t", "content": [{"type": "sorcery"}]},
         "content type"),
        ({"sessionUpdate": "tool_call_content_chunk", "toolCallId": "t", "content": {"type": "sorcery"}},
         "tool_call_content_chunk.content type"),
        ({"sessionUpdate": "tool_call_update", "toolCallId": "t",
          "content": [_diff_item(changes=[{"operation": "teleport", "path": "/a"}])]},
         "diff change operation"),
        ({"sessionUpdate": "tool_call_update", "toolCallId": "t",
          "content": [_diff_item(changes=[{"operation": "add", "path": "/a", "fileType": "ghost"}])]},
         "diff change fileType"),
        ({"sessionUpdate": "tool_call_update", "toolCallId": "t",
          "content": [_diff_item(patch={"format": "svn", "text": "x"})]},
         "diff patch format"),
        ({"sessionUpdate": "tool_call_content_chunk", "toolCallId": "t",
          "content": _diff_item(changes=[{"operation": "teleport", "path": "/a"}])},
         "diff change operation"),
        ({"sessionUpdate": "plan_update", "plan": {"type": "hologram", "planId": "p"}}, "plan type"),
        ({"sessionUpdate": "plan_update", "plan": {"type": "items", "planId": "p", "entries": [
            {"content": "c", "priority": "urgent", "status": "pending"}]}}, "plan entry priority"),
        ({"sessionUpdate": "available_commands_update",
          "availableCommands": [{"type": "macro", "name": "n", "description": "d"}]},
         "available command type"),
        ({"sessionUpdate": "state_update", "state": "busy"}, "state_update.state"),
        ({"sessionUpdate": "surprise"}, "sessionUpdate"),
    ],
)
def test_unprefixed_unknown_value_is_flagged_at_each_site(update, label):
    scan = _scan_update(update)
    assert len(scan.violations) == 1 and label in scan.violations[0], scan.violations


def test_chunk_content_object_is_not_iterated_as_a_list():
    """The chunk's `content` is one object: iterating it would yield key strings, so an unknown
    `type` there used to pass unnoticed."""
    update = {"sessionUpdate": "tool_call_content_chunk", "toolCallId": "t", "content": {"type": "sorcery"}}
    assert _scan_update(update).violations == ["tool_call_content_chunk.content type='sorcery'"]


def test_permission_request_options_and_subject_tool_call_are_scanned():
    scan = OpenEnumScan()
    scan.scan_permission_request(
        {
            "options": [{"optionId": "a", "name": "A", "kind": "allow_once"}],
            "subject": {
                "type": "tool_call",
                "toolCall": {"toolCallId": "t", "kind": "read", "status": "pending",
                             "content": [{"type": "diff", "changes": [{"operation": "add", "path": "/a"}]}]},
            },
        }
    )
    assert scan.violations == [] and scan.checked == 5

    bad = OpenEnumScan()
    bad.scan_permission_request(
        {
            "options": [{"optionId": "a", "name": "A", "kind": "sorcery"}],
            "subject": {"type": "tool_call", "toolCall": {"toolCallId": "t", "status": "sorcery"}},
        }
    )
    assert bad.violations == [
        "permission option kind='sorcery'",
        "permission subject toolCall.status='sorcery'",
    ]


def test_subject_type_itself_is_not_judged():
    scan = OpenEnumScan()
    scan.scan_permission_request({"options": [], "subject": {"type": "hologram"}})
    assert scan.checked == 0 and scan.violations == []


@pytest.mark.parametrize(
    "value",
    [
        "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
        "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-00",
        "01-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01-extra",
    ],
)
def test_valid_traceparent(value):
    assert is_valid_traceparent(value)


@pytest.mark.parametrize(
    "value",
    [
        "not-a-trace-id",
        "",
        None,
        123,
        "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331",  # no flags
        "00-0AF7651916CD43DD8448EB211C80319C-b7ad6b7169203331-01",  # uppercase hex
        "00-00000000000000000000000000000000-b7ad6b7169203331-01",  # all-zero trace id
        "00-0af7651916cd43dd8448eb211c80319c-0000000000000000-01",  # all-zero parent id
        "ff-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",  # version ff
        "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01-extra",  # v00 takes no suffix
        "01-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01x",  # suffix must follow `-`
    ],
)
def test_invalid_traceparent(value):
    assert not is_valid_traceparent(value)


_TRACEPARENT = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"


def test_judge_w3c_meta_skips_null_patch_removals():
    meta = {"traceparent": None, "tracestate": None, "baggage": None}
    assert judge_w3c_meta(meta) == (0, [])


def test_judge_w3c_meta_accepts_well_formed_values_and_flags_bad_ones():
    assert judge_w3c_meta({"traceparent": _TRACEPARENT, "tracestate": "a=b", "baggage": "k=v"}) == (3, [])
    judged, problems = judge_w3c_meta({"traceparent": "nope", "tracestate": 5, "baggage": None})
    assert judged == 2
    assert problems == ["traceparent='nope'", "tracestate=5"]


@pytest.mark.parametrize("key", ["com.example/requestId", "zed.dev/x", "com.example/y"])
def test_namespaced_meta_keys(key):
    assert is_namespaced_meta_key(key)


@pytest.mark.parametrize(
    "key",
    ["vendorThing", "tck", "example/x", "com.example/", "/x", "io.agentclientprotocol/x", ".example/x"],
)
def test_non_namespaced_meta_keys(key):
    assert not is_namespaced_meta_key(key)
