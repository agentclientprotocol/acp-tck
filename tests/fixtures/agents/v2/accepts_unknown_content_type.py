#!/usr/bin/env python3
"""Non-conforming fixture: accepts a prompt containing a `_tck_unknown` content block instead of
rejecting it with `-32602` (prompt-lifecycle.mdx:313). Unadvertised `image`/`audio`/`resource`
blocks are still rejected. FAILs `ACP-PROMPT-211` only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsUnknownContentTypeAgent(ConformingAgent):
    def _unsupported_content_rejection(self, prompt: list[Any]) -> tuple[int, str] | None:
        known = [
            block
            for block in prompt
            if isinstance(block, dict) and block.get("type") in {"text", "resource_link", "image", "audio", "resource"}
        ]
        return super()._unsupported_content_rejection(known)


def main() -> None:
    AcceptsUnknownContentTypeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
