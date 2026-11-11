#!/usr/bin/env python3
"""Non-conforming fixture: `session/new` carries `configOptions` but `session/resume` of that
session leaves them out (session-setup.mdx:108,333-335).

FAILs exactly `ACP-RESUME-210`. `ACP-CONFIG-203` SKIPs: with no list on the resume there is no
shape to validate.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeOmitsConfigOptionsAgent(ConformingAgent):
    def _resume_result(self) -> dict[str, Any]:
        return {}


def main() -> None:
    ResumeOmitsConfigOptionsAgent(
        capabilities={"session": {}},
        config_options=[
            {
                "configId": "verbosity",
                "name": "Verbosity",
                "type": "select",
                "currentValue": "normal",
                "options": [{"value": "quiet", "name": "Quiet"}, {"value": "normal", "name": "Normal"}],
            }
        ],
    ).run()


if __name__ == "__main__":
    main()
