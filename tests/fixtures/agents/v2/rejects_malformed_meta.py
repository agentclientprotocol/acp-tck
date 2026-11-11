#!/usr/bin/env python3
"""Non-conforming fixture: validates `session/prompt`'s `_meta` strictly and rejects a non-object
value with `-32602`, instead of treating it as omitted (`extensibility.mdx:74`).

FAILs `ACP-META-202` only; a prompt with an object `_meta` (`ACP-META-001`) is still accepted.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RejectsMalformedMetaAgent(ConformingAgent):
    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        meta = params.get("_meta")
        if meta is not None and not isinstance(meta, dict):
            self._error(msg_id, -32602, "Invalid params: _meta must be an object")
            return
        super()._handle_prompt(msg_id, params)


def main() -> None:
    RejectsMalformedMetaAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
