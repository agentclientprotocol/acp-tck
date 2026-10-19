#!/usr/bin/env python3
"""Non-conforming fixture: asks for permission with an option whose `kind` is an unrecognized
value that does *not* begin with `_` (`"sorcery"`).

FAILs only `ACP-ENUM-201` (`PermissionOptionKind`: custom kinds MUST begin with `_`).
Schema-valid on its own -- the `other` fallback branch accepts any string.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class UnprefixedCustomPermissionKindAgent(AsksPermissionAgent):
    def _permission_options(self) -> list[dict[str, Any]]:
        return [
            {"optionId": "allow-once", "name": "Allow", "kind": "allow_once"},
            {"optionId": "cast-spell", "name": "Cast a spell", "kind": "sorcery"},
        ]


def main() -> None:
    UnprefixedCustomPermissionKindAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
