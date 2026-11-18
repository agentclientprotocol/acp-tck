#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options` and `loadSession`, and
`session/options` with a `sessionId` it never issued is answered with the new-session options
instead of an error. Violates ACP-OPTIONS-003 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"loadSession": True, "sessionCapabilities": {"options": {}}}


class OptionsAcceptsUnknownSessionAgent(ConformingAgent):
    def _handle_options(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_options(msg_id, {k: v for k, v in params.items() if k != "sessionId"})


def main() -> None:
    OptionsAcceptsUnknownSessionAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-options-accepts-unknown-session"
    ).run()


if __name__ == "__main__":
    main()
