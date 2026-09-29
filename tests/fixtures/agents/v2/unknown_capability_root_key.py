#!/usr/bin/env python3
"""Non-conforming fixture: the `initialize` result's `capabilities` object carries a root key
(`"vendorFeature"`) that is not part of `AgentCapabilities` in the schema. It has no spec
home at all, so `ACP-EXT-202` (ADVISORY) must flag it.
`unknown_root_key.py` already covers the same defect at the *response* root; this fixture
targets `capabilities`'s own root instead, which is what `ACP-EXT-202` specifically checks.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(capabilities={"session": {}, "vendorFeature": {}}).run()


if __name__ == "__main__":
    main()
