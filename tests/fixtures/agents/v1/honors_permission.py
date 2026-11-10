#!/usr/bin/env python3
"""Conforming fixture for the permission probe (ACP-PERM-001/002): on a prompt that names
`tck-permission-probe.txt` it asks `session/request_permission` (allow_once / reject_once) and
creates that file in the session `cwd` only when the client selected `allow-once`. A rejected,
cancelled or unrecognised outcome leaves no file. Any other prompt resolves normally without a
permission request. Subclasses override `_should_run` to model defects.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from asks_permission import AsksPermissionAgent  # noqa: E402

PROBE_FILE = "tck-permission-probe.txt"


class HonorsPermissionAgent(AsksPermissionAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._probe_session_id: str | None = None

    def _should_run(self, outcome: dict[str, Any]) -> bool:
        """Whether the operation runs for the client's `outcome`."""
        return outcome.get("outcome") == "selected" and outcome.get("optionId") == "allow-once"

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        text = " ".join(
            block.get("text", "")
            for block in params.get("prompt") or []
            if isinstance(block, dict) and block.get("type") == "text"
        )
        session = self._sessions.get(params.get("sessionId"))
        if PROBE_FILE not in text or session is None:
            ConformingAgent._handle_prompt(self, msg_id, params)
            return
        self._probe_session_id = params["sessionId"]
        super()._handle_prompt(msg_id, params)

    def _handle_client_response(self, message: dict[str, Any]) -> None:
        pending = self._awaiting_permission
        if pending is not None and message.get("id") == pending["perm_id"]:
            outcome = (message.get("result") or {}).get("outcome") or {}
            session = self._sessions.get(self._probe_session_id)
            if session is not None and self._should_run(outcome):
                (Path(session["cwd"]) / PROBE_FILE).write_text("hello\n")
        super()._handle_client_response(message)


def main() -> None:
    HonorsPermissionAgent(agent_name="tck-fixture-honors-permission").run()


if __name__ == "__main__":
    main()
