#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.prompt.embeddedContext` but accepts an
embedded `resource` block that carries neither `text` nor `blob`, instead of rejecting it with
`-32602` (a closed site, `extensibility.mdx:242-245`). FAILs `ACP-ENUM-204` only; an ordinary
resource block is still accepted, so `ACP-PROMPTCAP-003` PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsContentlessEmbeddedResourceAgent(ConformingAgent):
    def _prompt_rejection(self, prompt: list[Any]) -> tuple[int, str] | None:
        return None


def main() -> None:
    AcceptsContentlessEmbeddedResourceAgent(
        capabilities={"session": {"prompt": {"embeddedContext": {}}}}
    ).run()


if __name__ == "__main__":
    main()
