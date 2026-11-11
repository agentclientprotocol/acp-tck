#!/usr/bin/env python3
"""Non-conforming fixture: advertises an unprefixed vendor key in `capabilities._meta`
(`{"vendorThing": true}`), a name `extensibility.mdx:102` reserves for ACP. FAILs `ACP-META-204`
only (ADVISORY).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(capabilities={"session": {}, "_meta": {"vendorThing": True}}).run()


if __name__ == "__main__":
    main()
