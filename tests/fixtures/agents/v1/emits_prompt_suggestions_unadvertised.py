#!/usr/bin/env python3
"""Non-conforming fixture: sends a (valid) `prompt_suggestions_update` on every prompt turn
although the client never advertised `clientCapabilities.session.promptSuggestions`. Violates
ACP-CLIENTCAP-008 only: on the connection that does advertise it, each prompt replaces the list
(ACP-SUGGEST-001..003 PASS).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _emits_update import EmitsUpdateAgent  # noqa: E402
from _suggests import TEXT_SUGGESTIONS  # noqa: E402


class EmitsPromptSuggestionsAgent(EmitsUpdateAgent):
    _update = {"sessionUpdate": "prompt_suggestions_update", "suggestions": TEXT_SUGGESTIONS}


def main() -> None:
    EmitsPromptSuggestionsAgent(agent_name="tck-fixture-emits-prompt-suggestions-unadvertised").run()


if __name__ == "__main__":
    main()
