"""Open-enum emitter sweep behind `ACP-ENUM-201`.

Walks the agent-authored values the suite can see in one turn -- `session/update` updates and
`session/request_permission` params -- and checks each open-enum site against its defined
constants (`tck.v2.protocol`). A site's value is legal when it is a defined constant or begins
with `_`: the schema's own `other` fallback accepts any string, so only this check catches a
custom non-underscore value (`extensibility.mdx:237-240`). A curated subset of the schema's
open-enum sites (`subject.type` is deliberately not checked).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .protocol import (
    AVAILABLE_COMMAND_TYPE,
    DIFF_FILE_TYPE,
    DIFF_OPERATION,
    DIFF_PATCH_FORMAT,
    PERMISSION_OPTION_KIND,
    PLAN_CONTENT_TYPE,
    PLAN_ENTRY_PRIORITY,
    PLAN_ENTRY_STATUS,
    SESSION_UPDATE_KIND,
    STATE_UPDATE_STATE,
    TOOL_CALL_CONTENT_TYPE,
    TOOL_CALL_STATUS,
    TOOL_KIND,
    is_valid_open_enum_value,
)


@dataclass
class OpenEnumScan:
    """Counts the open-enum values seen (`checked`) and the illegal ones (`violations`)."""

    checked: int = 0
    violations: list[str] = field(default_factory=list)

    def check(self, label: str, value: Any, defined: frozenset[str]) -> None:
        self.checked += 1
        if not is_valid_open_enum_value(value, defined):
            self.violations.append(f"{label}={value!r}")

    def scan_update(self, update: dict[str, Any]) -> None:
        """One `session/update` `update` object."""
        kind = update.get("sessionUpdate")
        if kind is None:
            return
        self.check("sessionUpdate", kind, SESSION_UPDATE_KIND)
        if kind == "state_update" and "state" in update:
            self.check("state_update.state", update["state"], STATE_UPDATE_STATE)
        elif kind == "tool_call_update":
            self._scan_tool_call("tool_call_update", update)
        elif kind == "tool_call_content_chunk":
            # A chunk's `content` is a single `ToolCallContent` object, not an array.
            self._scan_content_item("tool_call_content_chunk.content", update.get("content"))
        elif kind == "plan_update":
            self._scan_plan(update.get("plan"))
        elif kind == "available_commands_update":
            commands = update.get("availableCommands")
            for command in commands if isinstance(commands, list) else []:
                if isinstance(command, dict) and "type" in command:
                    self.check("available command type", command["type"], AVAILABLE_COMMAND_TYPE)

    def scan_permission_request(self, params: dict[str, Any]) -> None:
        """`session/request_permission` params: option kinds, and a `tool_call` subject's
        `toolCall`, which the client applies exactly like a `tool_call_update`
        (`tool-calls.mdx:270-273`)."""
        options = params.get("options")
        for option in options if isinstance(options, list) else []:
            if isinstance(option, dict) and "kind" in option:
                self.check("permission option kind", option["kind"], PERMISSION_OPTION_KIND)
        subject = params.get("subject")
        if isinstance(subject, dict) and subject.get("type") == "tool_call":
            tool_call = subject.get("toolCall")
            if isinstance(tool_call, dict):
                self._scan_tool_call("permission subject toolCall", tool_call)

    def _scan_tool_call(self, label: str, tool_call: dict[str, Any]) -> None:
        if tool_call.get("kind") is not None:
            self.check(f"{label}.kind", tool_call["kind"], TOOL_KIND)
        if tool_call.get("status") is not None:
            self.check(f"{label}.status", tool_call["status"], TOOL_CALL_STATUS)
        content = tool_call.get("content")
        for item in content if isinstance(content, list) else []:
            self._scan_content_item(f"{label}.content", item)

    def _scan_content_item(self, label: str, item: Any) -> None:
        if not isinstance(item, dict) or "type" not in item:
            return
        self.check(f"{label} type", item["type"], TOOL_CALL_CONTENT_TYPE)
        if item["type"] != "diff":
            return
        changes = item.get("changes")
        for change in changes if isinstance(changes, list) else []:
            if not isinstance(change, dict):
                continue
            if "operation" in change:
                self.check("diff change operation", change["operation"], DIFF_OPERATION)
            if change.get("fileType") is not None:
                self.check("diff change fileType", change["fileType"], DIFF_FILE_TYPE)
        patch = item.get("patch")
        if isinstance(patch, dict) and "format" in patch:
            self.check("diff patch format", patch["format"], DIFF_PATCH_FORMAT)

    def _scan_plan(self, plan: Any) -> None:
        if not isinstance(plan, dict):
            return
        if "type" in plan:
            self.check("plan type", plan["type"], PLAN_CONTENT_TYPE)
        entries = plan.get("entries")
        for entry in entries if isinstance(entries, list) else []:
            if not isinstance(entry, dict):
                continue
            if "priority" in entry:
                self.check("plan entry priority", entry["priority"], PLAN_ENTRY_PRIORITY)
            if "status" in entry:
                self.check("plan entry status", entry["status"], PLAN_ENTRY_STATUS)
