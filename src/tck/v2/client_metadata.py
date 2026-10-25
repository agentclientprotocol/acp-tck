"""Deterministic v2 client-state checks, separate from agent conformance.

Expected snapshots are literal protocol examples, never computed by a TCK reducer.
The adapter contract is documented in docs/client-metadata.md.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tck.common.harness import AgentLaunch, AgentProcess

SPEC = "https://github.com/agentclientprotocol/agent-client-protocol/blob/beac4ba96190018e9f6d82e148ff275084c5aa3e/docs/protocol/v2/draft/extensibility.mdx#metadata-patches"
ENTITY_FIELDS = {
    "tool_call_update": {"toolCallId": "entity-1", "title": "Metadata test"},
    "terminal_update": {"terminalId": "entity-1"},
    "user_message": {"messageId": "entity-1"},
    "agent_message": {"messageId": "entity-1"},
    "agent_thought": {"messageId": "entity-1"},
    "session_info_update": {},
    "compaction_update": {"compactionId": "entity-1", "status": "in_progress"},
    "subagent_update": {"sessionId": "child-1"},
    "session_message": {"messageId": "entity-1"},
}


@dataclass(frozen=True)
class Case:
    name: str
    # Each pair is an update's patch fields and the stored metadata after it.
    steps: tuple[tuple[dict[str, Any], dict[str, Any] | None], ...]


_AB = {"a": 1, "b": 2}
CASES = (
    Case("initial-omitted", (({}, None),)),
    Case("initial-clear", (({"_meta": None}, None),)),
    Case("initial-empty-object", (({"_meta": {}}, None),)),
    Case("omitted", (({"_meta": _AB}, _AB), ({}, _AB))),
    Case("clear", (({"_meta": _AB}, _AB), ({"_meta": None}, None))),
    Case("empty-object", (({"_meta": _AB}, _AB), ({"_meta": {}}, _AB))),
    Case("retain-keys", (({"_meta": _AB}, _AB), ({"_meta": {"a": 3}}, {"a": 3, "b": 2}))),
    Case("remove-key", (({"_meta": _AB}, _AB), ({"_meta": {"a": None}}, {"b": 2}))),
    Case("remove-absent-key", (({"_meta": {"a": None}}, None),)),
    Case("nested-replacement", (
        ({"_meta": {"a": {"x": 1, "y": 2}}}, {"a": {"x": 1, "y": 2}}),
        ({"_meta": {"a": {"x": 3}}}, {"a": {"x": 3}}),
    )),
    Case("array-replacement", (
        ({"_meta": {"a": [1, 2]}}, {"a": [1, 2]}),
        ({"_meta": {"a": [3]}}, {"a": [3]}),
    )),
    Case("nested-null-data", (({"_meta": {"a": {"x": None}}}, {"a": {"x": None}}),)),
    Case("unknown-keys", (
        ({"_meta": {"vendor.example/opaque": False}}, {"vendor.example/opaque": False}),
        ({"_meta": {"other.example/value": {}}},
         {"vendor.example/opaque": False, "other.example/value": {}}),
    )),
    Case("remove-last-key", (({"_meta": {"a": 1}}, {"a": 1}), ({"_meta": {"a": None}}, None))),
    Case("clear-then-object", (
        ({"_meta": {"stale": 1}}, {"stale": 1}),
        ({"_meta": None}, None),
        ({"_meta": {"current": 2}}, {"current": 2}),
    )),
    Case("replay-over-stale", (
        ({"_meta": {"stale": 1, "a": 0}}, {"stale": 1, "a": 0}),
        ({"_meta": {"stale": None, "a": 1, "b": 2}}, {"a": 1, "b": 2}),
        ({"_meta": {"a": None}}, {"b": 2}),
        ({"_meta": {"stale": None, "a": 1, "b": 2}}, {"a": 1, "b": 2}),
        ({"_meta": {"a": None}}, {"b": 2}),
    )),
)


def update_message(entity: str, patch: dict[str, Any]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "method": "session/update",
        "params": {
            "sessionId": "tck-metadata-session",
            # Envelope metadata is not entity metadata.
            "_meta": {"tck.example/notification": "do not retain"},
            "update": {"sessionUpdate": entity, **ENTITY_FIELDS[entity], **patch},
        },
    }


def _same_json(actual: Any, expected: Any) -> bool:
    """Compare JSON values without conflating booleans with numbers."""
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected) and actual == expected
    if isinstance(expected, dict):
        return (isinstance(actual, dict) and actual.keys() == expected.keys()
                and all(_same_json(actual[key], value) for key, value in expected.items()))
    if isinstance(expected, list):
        return (isinstance(actual, list) and len(actual) == len(expected)
                and all(_same_json(a, e) for a, e in zip(actual, expected)))
    return actual == expected


async def _request(process: AgentProcess, method: str, params: dict[str, Any]) -> Any:
    request_id = await process.send_request(method, params)
    entry = await process.wait_for_response(request_id)
    response = entry.parsed
    if (not isinstance(response, dict) or response.get("jsonrpc") != "2.0"
            or type(response.get("id")) is not int or response["id"] != request_id
            or "error" in response or "result" not in response):
        raise ValueError(f"adapter rejected {method}: {response!r}")
    return response["result"]


async def check(launch: AgentLaunch, entities: list[str]) -> dict[str, Any]:
    if not entities or any(entity not in ENTITY_FIELDS for entity in entities):
        raise ValueError("select at least one supported entity")
    results = []
    for entity in entities:
        for case in CASES:
            row = {"entity": entity, "case": case.name, "status": "PASS"}
            try:
                # A fresh process per case prevents one failed case contaminating another.
                async with AgentProcess(launch) as process:
                    reset = await _request(process, "_tck/reset", {"protocolVersion": 2, "entity": entity})
                    if reset != {}:
                        raise ValueError(f"expected an empty reset result, got {reset!r}")
                    for index, (patch, expected) in enumerate(case.steps, 1):
                        snapshot = await _request(process, "_tck/apply", {
                            "message": update_message(entity, patch),
                        })
                        if not isinstance(snapshot, dict) or set(snapshot) != {"_meta"}:
                            raise ValueError(f"step {index}: expected a result with only '_meta', got {snapshot!r}")
                        actual = snapshot["_meta"]
                        # Empty metadata and absent metadata are equivalent in the spec.
                        if actual == {}:
                            actual = None
                        if not _same_json(actual, expected):
                            raise ValueError(f"step {index}: expected {expected!r}, got {snapshot['_meta']!r}")
                if process.exit_code != 0:
                    raise ValueError(f"adapter exited with code {process.exit_code}")
            except Exception as exc:  # Report process/transport failures as failures too.
                row.update(status="FAIL", detail=str(exc))
            results.append(row)
    return {
        "suite": "v2-client-metadata",
        "specification": SPEC,
        "entities": entities,
        "results": results,
        "passed": bool(results) and all(row["status"] == "PASS" for row in results),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check an ACP v2 client's stored metadata through a test adapter.")
    parser.add_argument("--entity", action="append", choices=tuple(ENTITY_FIELDS), required=True,
                        help="Entity handled by the client adapter; repeat to test several.")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("pass the client adapter command after --")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    report = asyncio.run(check(AgentLaunch(command, default_timeout=args.timeout), list(dict.fromkeys(args.entity))))
    for row in report["results"]:
        print(f"{row['status']} {row['entity']}/{row['case']}" + (f": {row['detail']}" if "detail" in row else ""))
    if args.report_json:
        args.report_json.write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
