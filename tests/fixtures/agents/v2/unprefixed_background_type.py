#!/usr/bin/env python3
"""Non-conforming fixture: `reports_background_work.py`, except every `background` list also
carries an item whose `type` is `"task"`: not a defined type and not `_`-prefixed, so reserved
for future ACP variants (`BackgroundWork`'s `other` branch; prompt-lifecycle.mdx:209).

FAILs only `ACP-ENUM-201`. The `other` branch accepts any string, so schema validation does not
cascade, and `ACP-STATE-206..208` ignore items of other types.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UnprefixedBackgroundTypeAgent(ConformingAgent):
    def _with_background(self, session_id: Any, update: dict[str, Any]) -> dict[str, Any]:
        update = super()._with_background(session_id, update)
        return {**update, "background": [*update["background"], {"type": "task", "taskId": "job-1"}]}


def main() -> None:
    UnprefixedBackgroundTypeAgent(capabilities={"session": {}}, report_background_work=True).run()


if __name__ == "__main__":
    main()
