#!/usr/bin/env python3
"""Conforming fixture for the not-cancellable cancel rows' gate: a `__hang__` turn starts a live
tool call and terminal that advertise no `cancel` (`uncancellable_work`), and nothing ever
advertises `cancel`, so the agent may not implement `tool_call/cancel` or `terminal/cancel`
(both are `-32601` here, error.mdx:44). The TCK sends neither: every `ACP-TOOLCANCEL-*` and
`ACP-TERMCANCEL-*` row SKIPs, `-208` for the gate. Within the `-k` scope of the
`test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(capabilities={"session": {}}, uncancellable_work=True).run()


if __name__ == "__main__":
    main()
