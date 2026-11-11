"""Unit tests for pure helpers in `tck.common.plugin` that don't need a live agent process."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tck.common.plugin import (
    _TEST_PROPERTIES,
    _order_revokes_last,
    _status_markup,
    _verdict_reason,
    capability_is_supported,
    record_test_property,
)
from tck.common.report import Status, Verdict
from tck.common.requirements import Tier


def _tier_counts(*, mandatory_fail=0, mandatory_not_tested=0, capability_fail=0) -> dict:
    """A minimal `Verdict.tier_counts` shape -- only the MANDATORY/CAPABILITY entries
    `_verdict_reason` reads -- for the given non-zero counts."""
    zero = {status.value: 0 for status in Status}
    return {
        Tier.MANDATORY.value: {
            **zero,
            Status.FAIL.value: mandatory_fail,
            Status.NOT_TESTED.value: mandatory_not_tested,
        },
        Tier.CAPABILITY.value: {**zero, Status.FAIL.value: capability_fail},
    }


# --- object-marker semantics (default: present & non-null) ---


def test_object_marker_present_and_non_null_is_supported() -> None:
    result = {"agentCapabilities": {"mcpCapabilities": {"http": True}}}
    assert capability_is_supported(result, "agentCapabilities.mcpCapabilities") is True


def test_object_marker_empty_object_still_counts_as_supported() -> None:
    result = {"agentCapabilities": {"mcpCapabilities": {}}}
    assert capability_is_supported(result, "agentCapabilities.mcpCapabilities") is True


def test_object_marker_missing_is_not_supported() -> None:
    result = {"agentCapabilities": {}}
    assert capability_is_supported(result, "agentCapabilities.mcpCapabilities") is False


def test_object_marker_explicit_null_is_not_supported() -> None:
    result = {"agentCapabilities": {"mcpCapabilities": None}}
    assert capability_is_supported(result, "agentCapabilities.mcpCapabilities") is False


def test_object_marker_explicit_false_is_not_supported() -> None:
    # Schema-invalid, but must not count: e.g. `auth.logout: false` must not make the TCK call
    # `logout`.
    result = {"agentCapabilities": {"auth": {"logout": False}}}
    assert capability_is_supported(result, "agentCapabilities.auth.logout") is False


def test_object_marker_true_still_counts_as_supported() -> None:
    # Schema-invalid too, but only `false`/`null`/missing are excluded; v2's
    # `boolean_session_capability.py` self-test relies on `true` still gating tests in.
    result = {"capabilities": {"session": True}}
    assert capability_is_supported(result, "capabilities.session") is True


# --- boolean-gate semantics (boolean=True: only `=== true` counts) ---


def test_boolean_gate_true_is_supported() -> None:
    result = {"agentCapabilities": {"loadSession": True}}
    assert capability_is_supported(result, "agentCapabilities.loadSession", boolean=True) is True


def test_boolean_gate_false_is_not_supported() -> None:
    result = {"agentCapabilities": {"loadSession": False}}
    assert capability_is_supported(result, "agentCapabilities.loadSession", boolean=True) is False


def test_boolean_gate_missing_is_not_supported() -> None:
    result = {"agentCapabilities": {}}
    assert capability_is_supported(result, "agentCapabilities.loadSession", boolean=True) is False


def test_boolean_gate_non_boolean_truthy_value_is_not_supported() -> None:
    # A boolean gate is `=== true`, not merely truthy -- an object or a string there does not count.
    result = {"promptCapabilities": {"image": "yes"}}
    assert capability_is_supported(result, "promptCapabilities.image", boolean=True) is False


def test_nested_path_through_missing_intermediate_object() -> None:
    result = {}
    assert capability_is_supported(result, "agentCapabilities.loadSession", boolean=True) is False
    assert capability_is_supported(result, "agentCapabilities.mcpCapabilities") is False


# --- _verdict_reason: the NOT CONFORMANT reason string ---


def test_verdict_reason_mandatory_failures_only() -> None:
    verdict = Verdict(conformant=False, tier_counts=_tier_counts(mandatory_fail=3))
    assert _verdict_reason(verdict) == "3 mandatory failures"


def test_verdict_reason_singular_failure() -> None:
    verdict = Verdict(conformant=False, tier_counts=_tier_counts(mandatory_fail=1))
    assert _verdict_reason(verdict) == "1 mandatory failure"


def test_verdict_reason_mandatory_not_tested_only() -> None:
    verdict = Verdict(conformant=False, tier_counts=_tier_counts(mandatory_not_tested=21))
    assert _verdict_reason(verdict) == "21 mandatory not tested"


def test_verdict_reason_capability_failure_only() -> None:
    verdict = Verdict(conformant=False, tier_counts=_tier_counts(capability_fail=1))
    assert _verdict_reason(verdict) == "1 capability failure"


def test_verdict_reason_capability_failures_plural() -> None:
    verdict = Verdict(conformant=False, tier_counts=_tier_counts(capability_fail=2))
    assert _verdict_reason(verdict) == "2 capability failures"


def test_verdict_reason_mandatory_and_capability_failures_both_listed() -> None:
    verdict = Verdict(
        conformant=False,
        tier_counts=_tier_counts(mandatory_fail=3, mandatory_not_tested=21, capability_fail=1),
    )
    assert (
        _verdict_reason(verdict)
        == "3 mandatory failures, 21 mandatory not tested, 1 capability failure"
    )


def test_verdict_reason_blocked_by_auth() -> None:
    verdict = Verdict(conformant=False, tier_counts=_tier_counts(), blocked_by_auth=True)
    assert _verdict_reason(verdict) == "blocked by authentication"


def test_verdict_reason_blocked_by_version_mismatch() -> None:
    verdict = Verdict(
        conformant=False, tier_counts=_tier_counts(), blocked_by_version_mismatch=True
    )
    assert _verdict_reason(verdict) == "blocked by version mismatch"


def test_verdict_reason_failures_and_version_mismatch_combined() -> None:
    verdict = Verdict(
        conformant=False,
        tier_counts=_tier_counts(mandatory_fail=3, capability_fail=1),
        blocked_by_version_mismatch=True,
    )
    assert (
        _verdict_reason(verdict)
        == "3 mandatory failures, 1 capability failure, blocked by version mismatch"
    )


def test_verdict_reason_degenerate_no_cause_is_honest_not_empty() -> None:
    # Unreachable through `compute_verdict` (non-conformant always implies at least one of these
    # counts/flags is set), but `_verdict_reason` is a pure function of `Verdict` and must not
    # render empty parentheses if ever called with an inconsistent one.
    verdict = Verdict(conformant=False, tier_counts=_tier_counts())
    assert _verdict_reason(verdict) == "no cause recorded"


# --- _status_markup: per-requirement rows (no `count`) get their status's own colour ---


def test_status_markup_pass_is_green() -> None:
    assert _status_markup(Status.PASS) == {"green": True}


def test_status_markup_fail_is_red() -> None:
    assert _status_markup(Status.FAIL) == {"red": True}


def test_status_markup_skipped_is_yellow() -> None:
    assert _status_markup(Status.SKIPPED) == {"yellow": True}


def test_status_markup_not_tested_is_light() -> None:
    assert _status_markup(Status.NOT_TESTED) == {"light": True}


# --- _status_markup: tier-count summary lines (`count` given) -- zero renders plain ---


def test_status_markup_zero_count_is_unmarked_regardless_of_status() -> None:
    for status in Status:
        assert _status_markup(status, count=0) == {}


def test_status_markup_nonzero_count_keeps_status_colour() -> None:
    assert _status_markup(Status.PASS, count=4) == {"green": True}
    assert _status_markup(Status.FAIL, count=2) == {"red": True}
    assert _status_markup(Status.SKIPPED, count=17) == {"yellow": True}
    assert _status_markup(Status.NOT_TESTED, count=17) == {"light": True}


# --- record_test_property ---


def test_record_test_property_is_a_noop_outside_a_test_scope() -> None:
    record_test_property("k", "v")  # must not raise


def test_record_test_property_appends_to_the_scoped_list() -> None:
    props: list[tuple[str, object]] = []
    token = _TEST_PROPERTIES.set(props)
    try:
        record_test_property("k", "v")
    finally:
        _TEST_PROPERTIES.reset(token)
    assert props == [("k", "v")]


# --- `revokes` marker: ordering and the one-per-run limit ---


class _FakeItem:
    def __init__(self, name: str, *revokes: SimpleNamespace) -> None:
        self.nodeid = name
        self._revokes = list(revokes)

    def iter_markers(self, name: str) -> list[SimpleNamespace]:
        return self._revokes if name == "revokes" else []


_REVOKES = SimpleNamespace(args=("auth",), kwargs={"reason": "logout drops credentials"})


def test_revokes_item_moves_to_the_end_and_the_rest_keep_their_order() -> None:
    a, logout, b, c = _FakeItem("a"), _FakeItem("logout", _REVOKES), _FakeItem("b"), _FakeItem("c")
    items = [a, logout, b, c]
    assert _order_revokes_last(items) == []
    assert items == [a, b, c, logout]


def test_no_revokes_item_leaves_order_untouched() -> None:
    items = [_FakeItem("a"), _FakeItem("b")]
    before = list(items)
    assert _order_revokes_last(items) == []
    assert items == before


def test_two_revokes_items_are_an_error_and_nothing_is_reordered() -> None:
    first, mid, second = _FakeItem("one", _REVOKES), _FakeItem("mid"), _FakeItem("two", _REVOKES)
    items = [first, mid, second]
    errors = _order_revokes_last(items)
    assert len(errors) == 1 and "one" in errors[0] and "two" in errors[0]
    assert items == [first, mid, second]


def test_revokes_without_a_reason_is_an_error() -> None:
    bare = SimpleNamespace(args=("auth",), kwargs={})
    errors = _order_revokes_last([_FakeItem("x", bare)])
    assert len(errors) == 1 and "reason" in errors[0]


_REVOKES_TESTS = '''
import pytest

def test_first(): pass

@pytest.mark.revokes("auth", reason="drops credentials")
def test_revoker(): pass

def test_last(): pass
'''


@pytest.mark.parametrize("shim", ["tck.v1.plugin", "tck.v2.plugin"])
def test_version_shims_run_the_revokes_collection_hook(shim: str, tmp_path: Path) -> None:
    """The shims copy hooks by name, so this proves the marker's reordering and its
    one-per-run limit actually run under each `-p tck.v{1,2}.plugin`."""
    (tmp_path / "test_x.py").write_text(_REVOKES_TESTS)
    cmd = [sys.executable, "-m", "pytest", "-p", shim, "--collect-only", "-q", "-p", "no:cacheprovider"]
    ok = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    collected = [line for line in ok.stdout.splitlines() if "::" in line]
    assert [line.split("::")[1] for line in collected] == ["test_first", "test_last", "test_revoker"]

    (tmp_path / "test_y.py").write_text(_REVOKES_TESTS)
    bad = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
    assert bad.returncode != 0
    assert "at most one @pytest.mark.revokes test" in bad.stdout + bad.stderr
