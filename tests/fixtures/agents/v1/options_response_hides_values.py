#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options`, applies initial `configOptions`
entries, but the `session/new` response reports the option values from before they were applied.
A later `session/set_config_option` reveals the real values. Violates ACP-OPTIONS-011 only.
"""

import copy
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402


class OptionsResponseHidesValuesAgent(ConformingAgent):
    _reported: list[dict[str, Any]] | None = None

    def _apply_initial_config(self, params: dict[str, Any]) -> None:
        self._reported = copy.deepcopy(self._visible_config_options())
        super()._apply_initial_config(params)

    def _reply(self, msg_id: Any, result: dict[str, Any]) -> None:
        if self._reported is not None and "sessionId" in result and "configOptions" in result:
            result = dict(result, configOptions=self._reported)
            self._reported = None
        super()._reply(msg_id, result)


def main() -> None:
    OptionsResponseHidesValuesAgent(
        capabilities=CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-response-hides-values",
    ).run()


if __name__ == "__main__":
    main()
