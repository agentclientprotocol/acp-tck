#!/usr/bin/env python3
"""Non-conforming fixture: rejects `initialize` with `-32602` when the client's `capabilities`
(at the root or under `auth`) or `info` carry a property it does not recognize, instead of
ignoring it (initialization.mdx:134; extensibility.mdx:148). FAILs exactly `ACP-EXT-204`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

_KNOWN_CLIENT_CAPABILITIES = {"auth", "elicitation", "_meta"}
_KNOWN_AUTH_CAPABILITIES = {"terminal", "_meta"}
_KNOWN_INFO_FIELDS = {"name", "title", "version", "_meta"}


class RejectsUnknownCapabilityFieldsAgent(ConformingAgent):
    def _handle_initialize(self, msg_id: Any, params: dict[str, Any]) -> None:
        capabilities = params.get("capabilities") or {}
        auth = capabilities.get("auth") or {}
        info = params.get("info") or {}
        if (
            set(capabilities) - _KNOWN_CLIENT_CAPABILITIES
            or set(auth) - _KNOWN_AUTH_CAPABILITIES
            or set(info) - _KNOWN_INFO_FIELDS
        ):
            self._error(msg_id, -32602, "Invalid params: unknown field")
            return
        super()._handle_initialize(msg_id, params)


def main() -> None:
    RejectsUnknownCapabilityFieldsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
