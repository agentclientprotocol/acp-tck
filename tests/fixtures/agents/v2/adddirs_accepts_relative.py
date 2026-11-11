#!/usr/bin/env python3
"""Non-conforming fixture: advertises `session.additionalDirectories` but accepts a relative entry
instead of rejecting it with `-32602` (session-setup.mdx:443). FAILs exactly `ACP-ADDDIRS-203`;
`ACP-ADDDIRS-201/202` still PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AddDirsAcceptsRelativeAgent(ConformingAgent):
    def _additional_directories_rejection(self, directories: Any) -> str | None:
        return None


def main() -> None:
    AddDirsAcceptsRelativeAgent(capabilities={"session": {"additionalDirectories": {}}}).run()


if __name__ == "__main__":
    main()
