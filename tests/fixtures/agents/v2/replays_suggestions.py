#!/usr/bin/env python3
"""Non-conforming fixture: on a `session/resume` with `replayFrom`, replays the session's last
suggestion list as a `prompt_suggestions_update` right after `replay_complete`, before the resume
response. It otherwise behaves like a conforming suggesting agent. Violates ACP-SUGGEST-004 only.

The fixture base sends no `replay_complete` yet, so this fixture sends it itself, right before the
suggestion. Drop that once the base does.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _suggests import SuggestsMixin  # noqa: E402


class ReplaysSuggestionsAgent(SuggestsMixin, ConformingAgent):
    def _replay_history(self, session_id: Any) -> None:
        super()._replay_history(session_id)
        self._notify(
            "session/update", {"sessionId": session_id, "update": {"sessionUpdate": "replay_complete"}}
        )
        if self._suggestions_advertised() and self._current_suggestions.get(session_id):
            self._send_suggestions(session_id, list(self._current_suggestions[session_id]))


def main() -> None:
    ReplaysSuggestionsAgent(
        capabilities={"session": {}}, agent_name="tck-fixture-replays-suggestions"
    ).run()


if __name__ == "__main__":
    main()
