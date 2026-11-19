#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options` and silently ignores initial
`configOptions` entries that do not match the schema instead of failing the request with `-32602`.
Violates ACP-OPTIONS-004 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402


class OptionsAcceptsMalformedAgent(ConformingAgent):
    _validate_initial_config = False


def main() -> None:
    OptionsAcceptsMalformedAgent(
        capabilities=CAPABILITIES, config_options=config_options(), agent_name="tck-fixture-options-accepts-malformed"
    ).run()


if __name__ == "__main__":
    main()
