"""Shared mixin for fixtures that replay chunked entities beyond messages (ACP-RESUME-205): a
session message, a tool call's content, a terminal's output and a compaction's summary, each
rebuilt from chunks (session-setup.mdx:303-321).

The extra updates follow the base replay and never enter the session's history. A kind listed in
`UNPRIMED` is replayed without the whole-entity update that must open it; the others get it,
emptied. `ReplaysEntityChunksMixin.KINDS` names the chunk kinds replayed.
"""

from __future__ import annotations

from typing import Any

_TEXT = {"type": "text", "text": "chunk"}

# chunk kind -> (opening whole-entity update with the chunked field emptied, the chunk)
_PRIMERS: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
    "session_message_chunk": (
        {"sessionUpdate": "session_message", "messageId": "tck-msg", "content": []},
        {"sessionUpdate": "session_message_chunk", "messageId": "tck-msg", "content": _TEXT},
    ),
    "tool_call_content_chunk": (
        {"sessionUpdate": "tool_call_update", "toolCallId": "tck-tool", "content": []},
        {
            "sessionUpdate": "tool_call_content_chunk",
            "toolCallId": "tck-tool",
            "content": {"type": "content", "content": _TEXT},
        },
    ),
    "terminal_output_chunk": (
        {"sessionUpdate": "terminal_update", "terminalId": "tck-term", "output": {"data": ""}},
        {"sessionUpdate": "terminal_output_chunk", "terminalId": "tck-term", "data": "out"},
    ),
    "compaction_summary_chunk": (
        {
            "sessionUpdate": "compaction_update",
            "compactionId": "tck-compact",
            "status": "in_progress",
            "summary": [],
        },
        {"sessionUpdate": "compaction_summary_chunk", "compactionId": "tck-compact", "content": _TEXT},
    ),
}


class ReplaysEntityChunksMixin:
    KINDS: tuple[str, ...] = tuple(_PRIMERS)
    UNPRIMED: tuple[str, ...] = ()

    def _replay_history(self, session_id: Any) -> None:
        super()._replay_history(session_id)  # type: ignore[misc]
        for kind in self.KINDS:
            primer, chunk = _PRIMERS[kind]
            for update in (chunk,) if kind in self.UNPRIMED else (primer, chunk):
                self._notify("session/update", {"sessionId": session_id, "update": update})  # type: ignore[attr-defined]
