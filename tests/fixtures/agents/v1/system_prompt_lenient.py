#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.systemPrompt` but creates the session
for any `systemPrompt`, including an unsupported mode and non-text content, instead of
returning an error. Violates ACP-SYSPROMPT-002 and ACP-SYSPROMPT-003; ACP-SYSPROMPT-001 still
PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"systemPrompt": {}}}


class SystemPromptLenientAgent(ConformingAgent):
    def _system_prompt_error(self, system_prompt: Any) -> str | None:
        return None


def main() -> None:
    SystemPromptLenientAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-system-prompt-lenient").run()


if __name__ == "__main__":
    main()
