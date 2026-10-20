#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.systemPrompt` (append only) but
rejects every `systemPrompt`, including the `append` mode every advertising agent must support.

FAILs exactly `ACP-SYSPROMPT-201`. `ACP-SYSPROMPT-202` SKIPs: `override` is not advertised.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class SystemPromptRejectsAppendAgent(ConformingAgent):
    def _system_prompt_rejection(self, system_prompt: Any) -> str | None:
        return None if system_prompt is None else "systemPrompt is not supported"


def main() -> None:
    SystemPromptRejectsAppendAgent(capabilities={"session": {"systemPrompt": {}}}).run()


if __name__ == "__main__":
    main()
