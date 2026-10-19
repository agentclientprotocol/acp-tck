#!/usr/bin/env python3
"""Non-conforming fixture: answers an unsupported version with a well-formed `-32022`, but keeps
serving the connection afterwards -- a later `session/new` succeeds, although "A version-mismatch
error does not initialize the connection" (initialization.mdx:117). FAILs exactly `ACP-INIT-207`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class StartsSessionAfterMismatchAgent(ConformingAgent):
    def _reject_unsupported_version(self, msg_id: Any, requested: int) -> None:
        super()._reject_unsupported_version(msg_id, requested)
        self._init_rejected = False


def main() -> None:
    StartsSessionAfterMismatchAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
