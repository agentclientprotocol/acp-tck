#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options` and `fork` (no `loadSession` or
`resume`) and, on `session/fork` only, fails the request with `-32602` for an initial `configOptions`
entry whose `configId` is unknown, where it must ignore the entry. Violates ACP-OPTIONS-006 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402
from _options_config import FORK_CAPABILITIES, config_options  # noqa: E402


class OptionsForkRejectsUnknownEntryAgent(CursorsMixin, ConformingAgent):
    def _handle_fork(self, msg_id: Any, params: dict[str, Any]) -> None:
        known = {o.get("id") for o in self._visible_config_options() or []}
        unknown = [e.get("configId") for e in params.get("configOptions") or [] if isinstance(e, dict)]
        unknown = [config_id for config_id in unknown if isinstance(config_id, str) and config_id not in known]
        if unknown and self._initial_config_error(params.get("configOptions")) is None:
            self._error(msg_id, -32602, f"Invalid params: unknown configId {unknown[0]!r}")
            return
        super()._handle_fork(msg_id, params)


def main() -> None:
    OptionsForkRejectsUnknownEntryAgent(
        capabilities=FORK_CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-fork-rejects-unknown-entry",
    ).run()


if __name__ == "__main__":
    main()
