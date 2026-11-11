#!/usr/bin/env python3
"""Non-conforming fixture: validates `capabilities` strictly and answers `-32602` when it is not
an object, even for a request of a newer version than the agent selects -- which "MUST ignore
parameters it can't parse under the selected version instead of rejecting the request"
(initialization.mdx:131). FAILs exactly `ACP-INIT-214`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RejectsUnparseableNewerParamsAgent(ConformingAgent):
    def _handle_initialize(self, msg_id: Any, params: dict[str, Any]) -> None:
        if "capabilities" in params and not isinstance(params["capabilities"], dict):
            self._error(msg_id, -32602, "Invalid params: capabilities must be an object")
            return
        super()._handle_initialize(msg_id, params)


def main() -> None:
    RejectsUnparseableNewerParamsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
