#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.systemPrompt` and rejects a non-text
`systemPrompt` content block on `session/new`, but `session/resume` resumes the session anyway
(session-setup.mdx:477,481). An unsupported mode is still rejected on both. It persists
sessions so the control resume succeeds on a fresh process.

FAILs exactly `ACP-SYSPROMPT-003` (its `session/resume` probe). `ACP-SYSPROMPT-002` PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class SystemPromptResumeAcceptsNonTextAgent(ConformingAgent):
    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        system_prompt = params.get("systemPrompt")
        if isinstance(system_prompt, dict):
            # Drop the content (the mode is still validated), as if non-text blocks were ignored.
            params = {**params, "systemPrompt": {**system_prompt, "content": []}}
        super()._handle_resume_session(msg_id, params)


def main() -> None:
    SystemPromptResumeAcceptsNonTextAgent(
        capabilities={"session": {"systemPrompt": {}}}, persist_sessions=True
    ).run()


if __name__ == "__main__":
    main()
