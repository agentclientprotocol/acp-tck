#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options` and accepts initial
`configOptions` that name the same `configId` twice instead of failing the request with `-32602`.
Violates ACP-OPTIONS-005 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402


class OptionsAcceptsDuplicateAgent(ConformingAgent):
    _reject_duplicate_initial_config = False


def main() -> None:
    OptionsAcceptsDuplicateAgent(
        capabilities=CAPABILITIES, config_options=config_options(), agent_name="tck-fixture-options-accepts-duplicate"
    ).run()


if __name__ == "__main__":
    main()
