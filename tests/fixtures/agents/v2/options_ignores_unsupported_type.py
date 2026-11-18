#!/usr/bin/env python3
"""Fixture for ACP-OPTIONS-201 (INFORMATIONAL): advertises `capabilities.session.options` and ignores
an initial `configOptions` entry of an unsupported value `type` (session-config-options.mdx:581)
instead of failing the request with `-32602` (:579). Both readings are conforming as far as the TCK
can tell, so no row FAILs; the row records "ignored".
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402


class OptionsIgnoresUnsupportedTypeAgent(ConformingAgent):
    _reject_unsupported_initial_type = False


def main() -> None:
    OptionsIgnoresUnsupportedTypeAgent(
        capabilities=CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-ignores-unsupported-type",
    ).run()


if __name__ == "__main__":
    main()
