#!/usr/bin/env python3
"""Non-conforming fixture: sends its suggestion list once, after the first turn of a session, and
never replaces or withdraws it when later prompts are accepted. Violates ACP-SUGGEST-003 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _suggests import SuggestsMixin  # noqa: E402


class StaleSuggestionsAgent(SuggestsMixin, ConformingAgent):
    _resuggest = False


def main() -> None:
    StaleSuggestionsAgent(
        capabilities={"session": {}}, agent_name="tck-fixture-stale-suggestions"
    ).run()


if __name__ == "__main__":
    main()
