"""Non-conforming fixture: emits one JSON-RPC message over three stdout lines after EOF."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent


def main() -> None:
    ConformingAgent(capabilities={"session": {}}).run()
    message = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "_meta": {"tags": ["a", "b"]},
            "params": {
                "sessionId": "split-message",
                "update": {
                    "sessionUpdate": "state_update",
                    "state": "idle",
                    "stopReason": "end_turn",
                },
            },
        },
        indent=2,
    )
    for part in message.splitlines():
        print(part, flush=True)


if __name__ == "__main__":
    main()
