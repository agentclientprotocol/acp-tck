#!/usr/bin/env python3
"""Conforming fixture: advertises `capabilities.session.options` and reports a `usage_update` for
every new session, unrelated to initial `configOptions` entries. A plain `session/new` sends it
just after its response; when the request carries entries, applying them delays the response and
the update comes first. The same request without entries sends that kind too, so ACP-OPTIONS-008
does not attribute it to the entries and PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402

USAGE = {"sessionUpdate": "usage_update", "used": 0, "size": 200000}


class OptionsUsageOvertakesResponseAgent(ConformingAgent):
    _had_entries = False
    _created: str | None = None

    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._had_entries = bool(params.get("configOptions"))
        self._created = None
        try:
            super()._handle_new_session(msg_id, params)
        finally:
            had_entries, self._had_entries = self._had_entries, False
        if self._created is not None and not had_entries:
            self._notify("session/update", {"sessionId": self._created, "update": dict(USAGE)})

    def _before_new_response(self, session_id: str) -> None:
        self._created = session_id
        if self._had_entries:
            self._notify("session/update", {"sessionId": session_id, "update": dict(USAGE)})


def main() -> None:
    OptionsUsageOvertakesResponseAgent(
        capabilities=CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-usage-overtakes-response",
    ).run()


if __name__ == "__main__":
    main()
