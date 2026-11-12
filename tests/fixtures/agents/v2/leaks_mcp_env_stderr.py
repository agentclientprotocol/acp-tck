#!/usr/bin/env python3
"""Non-conforming (ADVISORY-only) fixture: `leaks_mcp_env.py` with the `stderr` leak channel. Trips
only `ACP-SESSION-006`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from leaks_mcp_env import main  # noqa: E402

if __name__ == "__main__":
    main("stderr")
