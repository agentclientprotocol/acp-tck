#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options`; `session/new` reports its
select option correctly but `session/options` declares the same value twice in it. Violates
ACP-CONFIG-210 only (through the `session/options` result).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402


class OptionsDuplicateSelectValuesAgent(ConformingAgent):
    def _options_result(self, params: dict[str, Any]) -> dict[str, Any]:
        options = config_options()
        options[0]["options"].append({"value": "fast", "name": "Fast again"})
        return {"configOptions": options}


def main() -> None:
    OptionsDuplicateSelectValuesAgent(
        capabilities=CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-duplicate-select-values",
    ).run()


if __name__ == "__main__":
    main()
