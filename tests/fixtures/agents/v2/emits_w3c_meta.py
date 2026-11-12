#!/usr/bin/env python3
"""Positive control: emits well-formed `_meta` everywhere `ACP-META-203`/`ACP-META-204` look -- a
valid `traceparent`/`tracestate`/`baggage` on a `session/update`, and a reverse-DNS namespaced
key in `capabilities._meta` and on the notification. Both rows must PASS (not SKIP).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class EmitsW3cMetaAgent(ConformingAgent):
    def _mid_turn_action(self, session_id: Any) -> bool:
        self._notify(
            "session/update",
            {
                "sessionId": session_id,
                "update": {"sessionUpdate": "_tck_custom_update"},
                "_meta": {
                    "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
                    "tracestate": "congo=t61rcWkgMzE",
                    "baggage": "userId=alice",
                    "com.example/tck": True,
                },
            },
        )
        return False  # fire-and-forget: finish the turn immediately, in the same call


def main() -> None:
    EmitsW3cMetaAgent(capabilities={"session": {}, "_meta": {"com.example/workspace": True}}).run()


if __name__ == "__main__":
    main()
