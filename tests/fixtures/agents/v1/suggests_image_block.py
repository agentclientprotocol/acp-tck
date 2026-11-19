#!/usr/bin/env python3
"""Non-conforming fixture: sends a prompt suggestion made of an `image` block to a client that
advertised only `session.promptSuggestions: {}` (text and `resource_link` blocks). The block is a
valid content block, so the suggestion is still a valid prompt. Violates ACP-SUGGEST-001 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _suggests import SuggestsMixin  # noqa: E402


class SuggestsImageBlockAgent(SuggestsMixin, ConformingAgent):
    _suggestion_list = [
        {"prompt": [{"type": "image", "data": "iVBORw0KGgo=", "mimeType": "image/png"}]},
    ]


def main() -> None:
    SuggestsImageBlockAgent(agent_name="tck-fixture-suggests-image-block").run()


if __name__ == "__main__":
    main()
