"""The client adapter runner detects reducer defects; fixtures are not SDK coverage."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tck.common.harness import AgentLaunch
from tck.v2 import client_metadata
from tck.v2.client_metadata import CASES, ENTITY_FIELDS, _same_json, check, main, update_message

ADAPTER = Path(__file__).parents[1] / "fixtures" / "clients" / "v2" / "metadata_adapter.py"


def _check(mode="correct", entities=None):
    launch = AgentLaunch([sys.executable, str(ADAPTER), mode], default_timeout=1)
    return asyncio.run(check(launch, list(ENTITY_FIELDS) if entities is None else entities))


def test_every_selected_entity_and_case_passes_for_fixture():
    report = _check()
    assert report["passed"]
    assert len(report["results"]) == len(ENTITY_FIELDS) * len(CASES)
    assert len({(row["entity"], row["case"]) for row in report["results"]}) == len(report["results"])


@pytest.mark.parametrize(("mode", "failed_case"), [
    ("replace", "retain-keys"),
    ("ignore-clear", "clear"),
    ("store-null", "remove-absent-key"),
    ("recursive", "nested-replacement"),
    ("envelope", "initial-omitted"),
    ("bad-snapshot", "initial-omitted"),
    ("error", "initial-omitted"),
])
def test_reducer_and_adapter_defects_fail(mode, failed_case):
    report = _check(mode, ["tool_call_update"])
    assert not report["passed"]
    row = next(row for row in report["results"] if row["case"] == failed_case)
    assert row["status"] == "FAIL"
    assert row["detail"]
    assert len(report["results"]) == len(CASES)  # Continue after a failed case.


def test_cli_writes_scoped_report_and_deduplicates_entities(tmp_path):
    path = tmp_path / "report.json"
    result = subprocess.run([
        sys.executable, "-m", "tck.v2.client_metadata",
        "--entity", "terminal_update", "--entity", "terminal_update",
        "--report-json", str(path), "--", sys.executable, str(ADAPTER),
    ], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    report = json.loads(path.read_text())
    assert report["entities"] == ["terminal_update"]
    assert len(report["results"]) == len(CASES)
    assert report["passed"]


def test_cli_returns_failure_for_whole_object_replacement():
    assert main(["--entity", "tool_call_update", "--", sys.executable, str(ADAPTER), "replace"]) == 1


@pytest.mark.parametrize("mode", ["exit", "silent", "wrong-version", "bad-reset", "boolean-id", "exit-after-eof"])
def test_process_and_protocol_failures_are_reported(monkeypatch, mode):
    monkeypatch.setattr(client_metadata, "CASES", CASES[:1])
    launch = AgentLaunch([sys.executable, str(ADAPTER), mode],
                         default_timeout=0.1, close_grace=0.1)
    report = asyncio.run(check(launch, ["tool_call_update"]))
    assert not report["passed"]
    assert report["results"][0]["status"] == "FAIL"
    assert report["results"][0]["detail"]


@pytest.mark.parametrize("args", [
    [], ["--entity", "plan_update"], ["--entity", "tool_call_update"],
    *[["--entity", "tool_call_update", "--timeout", value, "--", "unused"]
      for value in ["0", "-1", "nan", "inf"]],
])
def test_invalid_usage(args):
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == 2


def test_empty_entity_selection_is_not_a_vacuous_pass():
    with pytest.raises(ValueError, match="at least one"):
        _check(entities=[])


def test_json_comparison_preserves_types_and_accepts_object_order():
    assert not _same_json({"a": True}, {"a": 1})
    assert not _same_json({"a": 0}, {"a": False})
    assert _same_json({"b": [1.0], "a": None}, {"a": None, "b": [1]})


def test_every_supplied_update_is_valid_against_pinned_schema():
    schema_path = Path(__file__).parents[2] / "src/tck/v2/schema/schema.unstable.json"
    schema = json.loads(schema_path.read_text())
    validator = Draft202012Validator({"$ref": "#/$defs/UpdateSessionNotification", "$defs": schema["$defs"]})
    for entity in ENTITY_FIELDS:
        for case in CASES:
            for patch, _ in case.steps:
                validator.validate(update_message(entity, patch)["params"])
