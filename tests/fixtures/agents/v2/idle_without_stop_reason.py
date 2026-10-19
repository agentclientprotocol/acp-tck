#!/usr/bin/env python3
"""Fixture: the idle that ends an ordinary turn carries no `stopReason` (cancelled turns still
report `cancelled`). The stop reason is only SHOULD, so this FAILs exactly the ADVISORY
`ACP-STATE-204`; `ACP-STATE-201/202/203` PASS and the verdict stays CONFORMANT.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class IdleWithoutStopReasonAgent(ConformingAgent):
    def _stop_reason(self) -> None:  # type: ignore[override]
        return None


def main() -> None:
    IdleWithoutStopReasonAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
