#!/usr/bin/env python3
"""Non-conforming fixture: sends a prompt suggestion whose only content is whitespace-only text
(schema-valid, text is an allowed type). Violates ACP-SUGGEST-002 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _suggests import SuggestsMixin  # noqa: E402


class SuggestsBlankPromptAgent(SuggestsMixin, ConformingAgent):
    _suggestion_list = [{"prompt": [{"type": "text", "text": "   "}]}]


def main() -> None:
    SuggestsBlankPromptAgent(agent_name="tck-fixture-suggests-blank-prompt").run()


if __name__ == "__main__":
    main()
