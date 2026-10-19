"""Shared base for defect fixtures that send one extra, schema-valid `session/update` on every
`session/prompt` for a known session, just before the normal turn (ACP-CLIENTCAP-004/006/007,
ACP-PROMPT-004). Each fixture script sets `_update` and runs its subclass.
"""

from __future__ import annotations

from typing import Any

from _base import ConformingAgent


class EmitsUpdateAgent(ConformingAgent):
    _update: dict[str, Any] = {}

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id in self._sessions:
            self._notify("session/update", {"sessionId": session_id, "update": dict(self._update)})
        super()._handle_prompt(msg_id, params)
