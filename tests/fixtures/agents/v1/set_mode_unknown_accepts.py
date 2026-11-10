#!/usr/bin/env python3
"""Non-conforming fixture: advertises modes and accepts `session/set_mode` for a `modeId` it never
offered, instead of `-32602`. Violates ACP-ERROR-007 only (it advertises no config options, so
the `session/set_config_option` probes SKIP).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

MODES = {
    "currentModeId": "default",
    "availableModes": [
        {"id": "default", "name": "Default"},
        {"id": "yolo", "name": "YOLO"},
    ],
}


class SetModeUnknownAcceptsAgent(ConformingAgent):
    _validate_set_params = False


def main() -> None:
    SetModeUnknownAcceptsAgent(
        agent_name="tck-fixture-set-mode-unknown-accepts", modes=dict(MODES)
    ).run()


if __name__ == "__main__":
    main()
