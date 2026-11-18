#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options` and `fork` and, on `session/fork`
only, fails the request with `-32602` for an initial `configOptions` entry whose `configId` is
unknown, where it must ignore the entry. Violates ACP-OPTIONS-006 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import FORK_CAPABILITIES, config_options  # noqa: E402


class OptionsForkRejectsUnknownEntryAgent(ConformingAgent):
    def _handle_fork_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        known = {o.get("configId") for o in self._config_options}
        entries = params.get("configOptions") or []
        unknown = [e.get("configId") for e in entries if isinstance(e, dict) and e.get("configId") not in known]
        if unknown and self._initial_config_error(entries) is None:
            self._error(msg_id, -32602, f"Invalid params: unknown configId {unknown[0]!r}")
            return
        super()._handle_fork_session(msg_id, params)


def main() -> None:
    OptionsForkRejectsUnknownEntryAgent(
        capabilities=FORK_CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-fork-rejects-unknown-entry",
    ).run()


if __name__ == "__main__":
    main()
