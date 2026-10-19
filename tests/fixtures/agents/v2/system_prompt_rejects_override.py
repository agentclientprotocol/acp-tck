#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.systemPrompt.mode.override` but
rejects an `override` `systemPrompt`; `append` works.

FAILs exactly `ACP-SYSPROMPT-202`. `ACP-SYSPROMPT-201` PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class SystemPromptRejectsOverrideAgent(ConformingAgent):
    def _system_prompt_rejection(self, system_prompt: Any) -> str | None:
        if isinstance(system_prompt, dict) and system_prompt.get("mode") == "override":
            return "override mode is not supported"
        return super()._system_prompt_rejection(system_prompt)


def main() -> None:
    SystemPromptRejectsOverrideAgent(
        capabilities={"session": {"systemPrompt": {"mode": {"override": {}}}}}
    ).run()


if __name__ == "__main__":
    main()
