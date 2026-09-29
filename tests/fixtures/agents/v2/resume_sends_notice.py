#!/usr/bin/env python3
"""Conforming fixture: sends a live `notice` `session/update` right after answering
`session/resume`, which the draft permits at any point in a session, and advertises the draft's
extra capability fields (`nes: {}`, `providers: {}`, `positionEncoding: "utf-16"`).

Fully conformant: `ACP-RESUME-202` must not treat the trailing `notice` as replayed history, and
`ACP-INIT-204` must not judge the scalar `positionEncoding` as an object marker.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeSendsNoticeAgent(ConformingAgent):
    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_resume_session(msg_id, params)
        self._notify(
            "session/update",
            {
                "sessionId": params.get("sessionId"),
                "update": {
                    "sessionUpdate": "notice",
                    "severity": "info",
                    "title": "Session resumed",
                },
            },
        )


def main() -> None:
    ResumeSendsNoticeAgent(
        capabilities={
            "session": {},
            "nes": {},
            "providers": {},
            "positionEncoding": "utf-16",
        }
    ).run()


if __name__ == "__main__":
    main()
