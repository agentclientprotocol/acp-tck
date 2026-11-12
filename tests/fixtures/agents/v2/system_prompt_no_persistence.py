#!/usr/bin/env python3
"""Fixture for the "cannot judge" path: advertises `capabilities.session.systemPrompt` and
refuses unsupported `systemPrompt`s correctly, but keeps sessions only in memory, so a fresh
process answers `session/resume` of an earlier session with `-32002`.

`ACP-SYSPROMPT-002`/`003`'s `session/new` probes PASS; their `session/resume` probes SKIP
("cannot judge": the control resume without a `systemPrompt` fails too). No FAIL.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(capabilities={"session": {"systemPrompt": {}}}).run()


if __name__ == "__main__":
    main()
