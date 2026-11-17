#!/usr/bin/env python3
"""Conforming fixture: `rejects_repeat_cancel_while_cancelling.py`, except accepting a request
for a not-cancellable item starts no new cancellable item. The only item that advertises
`capabilities.cancel` while live is then the one the TCK's not-cancellable request already went to,
which the main request never repeats: `-201/202` SKIP, naming that reason, and nothing FAILs.
Within the `-k` scope of the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rejects_repeat_cancel_while_cancelling import RejectsRepeatCancelWhileCancellingAgent  # noqa: E402


class RejectsRepeatCancelWithoutReplacementAgent(RejectsRepeatCancelWhileCancellingAgent):
    start_replacement = False


def main() -> None:
    RejectsRepeatCancelWithoutReplacementAgent(
        capabilities={"session": {}}, cancellable_work=True, uncancellable_work=True
    ).run()


if __name__ == "__main__":
    main()
