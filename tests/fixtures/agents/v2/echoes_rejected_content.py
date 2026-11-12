#!/usr/bin/env python3
"""Non-conforming fixture: answers an unknown or unadvertised prompt content block with the
required `-32602`, but only after inserting the prompt (a `user_message` echo and a `running`
update), which a rejection before insertion must not do (prompt-lifecycle.mdx:313,388). FAILs
`ACP-PROMPT-211` and `ACP-PROMPTCAP-201`. The turn it started is closed with an `idle`, so no
other row is affected.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class EchoesRejectedContentAgent(ConformingAgent):
    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        prompt = params.get("prompt") or []
        if session_id in self._sessions and self._unsupported_content_rejection(prompt) is not None:
            self._send_user_message_update(session_id, "msg-rejected", prompt)
            self._send_running_update(session_id)
            self._send_idle_update(session_id, "refusal")
        super()._handle_prompt(msg_id, params)


def main() -> None:
    EchoesRejectedContentAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
