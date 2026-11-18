#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.prompt.skill` but accepts a `skill`
block naming no skill it lists, instead of rejecting the prompt with `-32602`
(slash-commands.mdx:255). FAILs `ACP-PROMPTCAP-202` only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsUnknownSkillAgent(ConformingAgent):
    def _unknown_skill_rejection(self, prompt: list[Any]) -> tuple[int, str] | None:
        return None


def main() -> None:
    AcceptsUnknownSkillAgent(
        capabilities={"session": {"prompt": {"skill": {}}}},
        agent_name="tck-fixture-accepts-unknown-skill",
    ).run()


if __name__ == "__main__":
    main()
