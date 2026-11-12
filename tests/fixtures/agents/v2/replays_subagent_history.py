#!/usr/bin/env python3
"""Conforming fixture: `exposes_subagent.py`'s child per turn, and `session/resume` replays that
child's history under the child's own `sessionId`, announced by a `subagent_update` on the
resumed session first. The replayed child history also holds a `user_message` carrying the
parent's prompt text under its own `messageId` (the child's task, not the parent's message).
Every resume, with or without replay, emits live child chunks before the response. Must PASS
everything `exposes_subagent.py` does, including `ACP-RESUME-002` and `-205` (live child traffic
is not history or replayed chunks of the resumed session), `ACP-RESUME-204` (a child's own
`user_message` is not the parent's) and `ACP-RESUME-209` (announced child updates are legal
during replay).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ReplaysSubagentHistoryAgent(ExposesSubagentAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._children: dict[Any, list[str]] = {}  # parent sessionId -> child sessionIds
        self._last_prompt: Any = None

    def _send_user_message_update(self, session_id: Any, message_id: str, prompt: Any) -> None:
        self._last_prompt = prompt
        super()._send_user_message_update(session_id, message_id, prompt)

    def _mid_turn_action(self, session_id: Any) -> bool:
        result = super()._mid_turn_action(session_id)
        self._children.setdefault(session_id, []).append(f"{session_id}-child-{self._child_count}")
        return result

    def _replay_history(self, session_id: Any) -> None:
        super()._replay_history(session_id)
        for child_id in self._children.get(session_id, []):
            self._notify(
                "session/update",
                {
                    "sessionId": session_id,
                    "update": {
                        "sessionUpdate": "subagent_update",
                        "sessionId": child_id,
                        "title": "helper",
                    },
                },
            )
            self._notify(
                "session/update",
                {
                    "sessionId": child_id,
                    "update": {
                        "sessionUpdate": "user_message",
                        "messageId": f"{child_id}-task",
                        "content": self._last_prompt,
                    },
                },
            )
            super()._replay_history(child_id)

    def _send_resume_snapshot(self, session_id: Any) -> None:
        for child_id in self._children.get(session_id, []):
            # Live child traffic, addressed to the child and not recorded into history.
            self._notify(
                "session/update",
                {
                    "sessionId": child_id,
                    "update": {
                        "sessionUpdate": "agent_message_chunk",
                        "messageId": f"{child_id}-live",
                        "content": {"type": "text", "text": "child still working"},
                    },
                },
            )
        super()._send_resume_snapshot(session_id)


def main() -> None:
    ReplaysSubagentHistoryAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
