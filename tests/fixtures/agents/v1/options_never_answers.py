#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options` but never answers
`session/options`. Violates ACP-OPTIONS-001, and every row that needs a working `session/options`
FAILs on the timeout too; within `-k test_session_config` it FAILs nothing: ACP-CONFIG-003 judges
the payloads it got (its boolean option stays hidden from a client without the capability) and
does not FAIL on the unanswered call.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402


class OptionsNeverAnswersAgent(ConformingAgent):
    def _handle_options(self, msg_id: Any, params: dict[str, Any]) -> None:
        pass


def main() -> None:
    OptionsNeverAnswersAgent(
        capabilities=CAPABILITIES, config_options=config_options(), agent_name="tck-fixture-options-never-answers"
    ).run()


if __name__ == "__main__":
    main()
