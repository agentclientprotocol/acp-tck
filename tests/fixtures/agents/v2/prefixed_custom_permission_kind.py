#!/usr/bin/env python3
"""Positive control: asks for permission with an option whose `kind` is a `_`-prefixed custom
value (`"_tck_custom_kind"`) -- legal per the open-enum extensibility rule. Must PASS
`ACP-ENUM-201`. Paired with `unprefixed_custom_permission_kind.py`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class PrefixedCustomPermissionKindAgent(AsksPermissionAgent):
    def _permission_options(self) -> list[dict[str, Any]]:
        return [
            {"optionId": "allow-once", "name": "Allow", "kind": "allow_once"},
            {"optionId": "cast-spell", "name": "Cast a spell", "kind": "_tck_custom_kind"},
        ]


def main() -> None:
    PrefixedCustomPermissionKindAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
