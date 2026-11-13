#!/usr/bin/env python3
"""Conforming fixture: advertises `capabilities.session.fork` and reports background work that
stays listed for the rest of the session (`background_outlives_turn="keep"`): one background
tool call per session, still listed on the idle, through a `__hang__` turn's `session/cancel`
(not covered by it, prompt-lifecycle.mdx:1173) and absent from a fork's snapshots
(session-setup.mdx:49). The positive control for `ACP-FORK-206` and, with `--cancel-prompt
__hang__`, `ACP-INFO-BACKGROUND-202`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(
        capabilities={"session": {"fork": {}}},
        report_background_work=True,
        background_outlives_turn="keep",
    ).run()


if __name__ == "__main__":
    main()
