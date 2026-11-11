#!/usr/bin/env python3
"""Non-conforming fixture: a grouped `select` declares the value `normal` in two groups
(session-config-options.mdx:128-130: each `value` MUST be unique within the option, including
across groups). `currentValue` is `normal`, so `ACP-CONFIG-204` still PASSes. FAILs exactly
`ACP-CONFIG-210`; the shape is schema-valid.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

_VERBOSITY_OPTION = {
    "configId": "verbosity",
    "name": "Verbosity",
    "type": "select",
    "currentValue": "normal",
    "options": [
        {
            "groupId": "low",
            "name": "Low",
            "options": [{"value": "quiet", "name": "Quiet"}, {"value": "normal", "name": "Normal"}],
        },
        {
            "groupId": "high",
            "name": "High",
            "options": [{"value": "normal", "name": "Normal again"}, {"value": "verbose", "name": "Verbose"}],
        },
    ],
}


def main() -> None:
    ConformingAgent(capabilities={"session": {}}, config_options=[dict(_VERBOSITY_OPTION)]).run()

if __name__ == "__main__":
    main()
