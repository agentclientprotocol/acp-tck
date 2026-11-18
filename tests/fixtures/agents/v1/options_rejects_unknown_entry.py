#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options` and fails the request with
`-32602` for an initial `configOptions` entry whose `configId` is unknown, where it must ignore the
entry. Violates ACP-OPTIONS-006 only (malformed and duplicate entries are still rejected).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402


class OptionsRejectsUnknownEntryAgent(ConformingAgent):
    def _initial_config_error(self, entries: Any) -> str | None:
        error = super()._initial_config_error(entries)
        if error is not None:
            return error
        known = {o.get("id") for o in self._visible_config_options() or []}
        for entry in entries or []:
            if entry.get("configId") not in known:
                return f"unknown configId {entry.get('configId')!r}"
        return None


def main() -> None:
    OptionsRejectsUnknownEntryAgent(
        capabilities=CAPABILITIES, config_options=config_options(), agent_name="tck-fixture-options-rejects-unknown-entry"
    ).run()


if __name__ == "__main__":
    main()
