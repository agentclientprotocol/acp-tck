#!/usr/bin/env python3
"""Non-conforming fixture: `asks_permission.py`, but its permission request carries a `command`
subject whose `cwd` is a relative path. A command subject's `cwd` MUST be absolute
(tool-calls.mdx:302-303), and `AbsolutePath` is a plain string in the schema: FAILs exactly
`ACP-PERM-202`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class PermissionCommandRelativeCwdAgent(AsksPermissionAgent):
    def _permission_subject(self) -> dict[str, Any] | None:
        return {"type": "command", "command": "make test", "cwd": "build"}


def main() -> None:
    PermissionCommandRelativeCwdAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
