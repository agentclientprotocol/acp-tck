#!/usr/bin/env python3
"""Conforming-but-unjudgeable fixture: advertises `loadSession`, `sessionCapabilities.resume` and
`sessionCapabilities.systemPrompt`, but keeps sessions in memory only, so a fresh process
answers `session/load`/`session/resume` of an earlier session with `-32002`. The load/resume
probes of ACP-SYSPROMPT-002/003 cannot tell a refused systemPrompt from an unknown session, so
they SKIP; nothing FAILs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {
    "loadSession": True,
    "sessionCapabilities": {"resume": {}, "systemPrompt": {}},
}


def main() -> None:
    ConformingAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-system-prompt-no-restore").run()


if __name__ == "__main__":
    main()
