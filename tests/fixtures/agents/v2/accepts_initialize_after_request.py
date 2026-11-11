#!/usr/bin/env python3
"""Non-conforming fixture: answers an `initialize` repeated after another request with a result
instead of rejecting it (error.mdx:60). FAILs exactly `ACP-INIT-213`; `ACP-INIT-215` SKIPs
because there is no error to check the code of.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsInitializeAfterRequestAgent(ConformingAgent):
    _reject_late_initialize = False


def main() -> None:
    AcceptsInitializeAfterRequestAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
