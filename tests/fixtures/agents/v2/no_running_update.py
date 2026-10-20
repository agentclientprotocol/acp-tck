#!/usr/bin/env python3
"""Non-conforming fixture: skips `state_update {state: "running"}` entirely and jumps straight
to a turn-ending idle carrying `stopReason: "end_turn"`.

FAILs exactly `ACP-STATE-201`: `run_prompt` can only end the turn through its confirmed
fallback (a stopReason-bearing idle with no active state before it). `ACP-STATE-202` SKIPs ("no
foreground work observed"); `ACP-STATE-203` still judges the idle's `end_turn` and PASSes.
`ACP-PROMPT-201`/`ACP-PROMPT-203`/`ACP-PROMPT-205` are unaffected.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class NoRunningUpdateAgent(ConformingAgent):
    def _send_running_update(self, session_id: Any) -> None:
        pass  # deliberately omitted


def main() -> None:
    NoRunningUpdateAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
