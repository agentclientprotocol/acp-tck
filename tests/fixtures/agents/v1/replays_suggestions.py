#!/usr/bin/env python3
"""Non-conforming fixture: advertises `loadSession` and, inside the `session/load` exchange (before
its response), replays the session's last suggestion list as a `prompt_suggestions_update`. It
otherwise behaves like a conforming suggesting agent. Violates ACP-SUGGEST-004 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _suggests import SuggestsMixin  # noqa: E402

CAPABILITIES = {"loadSession": True}


class ReplaysSuggestionsAgent(SuggestsMixin, ConformingAgent):
    def _handle_load(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if self._suggestions_advertised() and session_id in self._sessions:
            self._send_suggestions(session_id, list(self._suggestion_list))
        super()._handle_load(msg_id, params)


def main() -> None:
    ReplaysSuggestionsAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-replays-suggestions").run()


if __name__ == "__main__":
    main()
