#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options` but answers every
`session/options` with an internal error instead of a result. Violates ACP-OPTIONS-001 only
(the other `session/options` rows judge nothing a failed call could break, or SKIP on it).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"options": {}}}


class OptionsMethodErrorsAgent(ConformingAgent):
    def _handle_options(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32603, "Internal error")


def main() -> None:
    OptionsMethodErrorsAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-options-method-errors").run()


if __name__ == "__main__":
    main()
