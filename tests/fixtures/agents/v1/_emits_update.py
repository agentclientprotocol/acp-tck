"""Shared base for defect fixtures that send one extra, schema-valid `session/update` on every
`session/prompt` for a known session, just before the normal turn (ACP-CLIENTCAP-004/006/007,
ACP-PROMPT-004, ACP-PLAN-001/002). Each fixture script sets `_update` (or overrides
`_build_update`) and runs its subclass. A fixture can set `_only_with_client_capability` to send
the update only when the client advertised that `clientCapabilities` key.
"""

from __future__ import annotations

from typing import Any

from _base import ConformingAgent


class EmitsUpdateAgent(ConformingAgent):
    _update: dict[str, Any] = {}
    _only_with_client_capability: str | None = None

    def _build_update(self, session_id: str) -> dict[str, Any]:
        return dict(self._update)

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        gate = self._only_with_client_capability
        if session_id in self._sessions and (gate is None or gate in self._client_capabilities):
            self._notify(
                "session/update", {"sessionId": session_id, "update": self._build_update(session_id)}
            )
        super()._handle_prompt(msg_id, params)
