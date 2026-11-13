#!/usr/bin/env python3
"""Conforming fixture: `replays_subagent_history.py`, and `session/load` also replays two recorded
entries of the parent's history that name a session the agent never exposed, so no announcement
exists for it: a directed `session_message` whose recipient is that session, and a tool call whose
`session` content references it. A replayed historical address is not an announcement and a
replayed reference to an unavailable session follows the historical replay rules (RFD), so every
`ACP-SUBAGENT-*` row PASSes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ReplaysHistoricalAddressesAgent(ExposesSubagentAgent):
    replay_on_load = True

    def _replayed_updates(self, logged):
        parent = logged[0][0]
        unavailable = f"{parent}-unavailable"
        message = {
            "sessionUpdate": "session_message",
            "messageId": f"{parent}-historical-task",
            "senderSessionId": parent,
            "recipientSessionId": unavailable,
            "content": [{"type": "text", "text": "a task for a session whose history is gone"}],
        }
        reference = {
            "sessionUpdate": "tool_call_update",
            "toolCallId": f"{parent}-historical-spawn",
            "title": "Spawn helper",
            "kind": "other",
            "status": "completed",
            "content": [{"type": "session", "sessionId": unavailable}],
        }
        return [*logged, (parent, message), (parent, reference)]


def main() -> None:
    ReplaysHistoricalAddressesAgent(
        capabilities={"loadSession": True}, agent_name="tck-fixture-replays-historical-addresses"
    ).run()


if __name__ == "__main__":
    main()
