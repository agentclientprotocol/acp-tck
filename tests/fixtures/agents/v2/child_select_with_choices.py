#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), except the select
config option reported for the child offers a second value besides its current one, as if the
Client could pick between them. The update is schema-valid (`currentValue` is among the options),
so FAILs exactly `ACP-SUBAGENT-014` (an ADVISORY row: the verdict is unchanged).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildSelectWithChoicesAgent(ExposesSubagentAgent):
    def _child_select_option(self):
        option = super()._child_select_option()
        option["options"] = [*option["options"], {"value": "m2", "name": "Model two"}]
        return option


def main() -> None:
    ChildSelectWithChoicesAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
