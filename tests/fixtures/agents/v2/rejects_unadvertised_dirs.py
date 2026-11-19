#!/usr/bin/env python3
"""Non-conforming fixture: does not advertise `session.additionalDirectories` but rejects a
`session/new` that carries the field with `-32602`, instead of ignoring it (session-setup.mdx:528).
FAILs exactly the ADVISORY `ACP-ADDDIRS-204`; the `ACP-ADDDIRS-001/202/203` rows SKIP (the
capability is not advertised).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RejectsUnadvertisedDirsAgent(ConformingAgent):
    def _additional_directories_rejection(self, directories: Any) -> str | None:
        if directories:
            return "additionalDirectories is not supported"
        return None


def main() -> None:
    RejectsUnadvertisedDirsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
