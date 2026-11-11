#!/usr/bin/env python3
"""Non-conforming fixture: advertises no `capabilities.session.prompt.*` capability, yet accepts
`image`, `audio` and `resource` blocks instead of rejecting them with `-32602`
(prompt-lifecycle.mdx:313). An unknown `_tck_unknown` block is still rejected. FAILs
`ACP-PROMPTCAP-201` only (its `image`, `audio` and `resource` cases).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsUnadvertisedContentAgent(ConformingAgent):
    def _unsupported_content_rejection(self, prompt: list[Any]) -> tuple[int, str] | None:
        # Treat every known type as supported; only unknown types are refused.
        unknown = [
            block
            for block in prompt
            if not (isinstance(block, dict) and block.get("type") in {"text", "resource_link", "image", "audio", "resource"})
        ]
        return super()._unsupported_content_rejection(unknown)


def main() -> None:
    AcceptsUnadvertisedContentAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
