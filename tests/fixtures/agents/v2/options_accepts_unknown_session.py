#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options`, and `session/options` with a
`sessionId` it never issued is answered with the new-session options instead of `-32002`. Violates
ACP-OPTIONS-003 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES  # noqa: E402


class OptionsAcceptsUnknownSessionAgent(ConformingAgent):
    def _handle_options(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_options(msg_id, {k: v for k, v in params.items() if k != "sessionId"})


def main() -> None:
    OptionsAcceptsUnknownSessionAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-options-accepts-unknown-session"
    ).run()


if __name__ == "__main__":
    main()
