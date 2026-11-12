#!/usr/bin/env python3
"""Non-conforming fixture: the JSON-RPC 2.0 batching behavior ACP v2 removed. An empty array gets
the single `-32600` object, but a non-empty one is dispatched element by element and answered
with one array of the responses (nothing at all if every element was a notification), a
malformed element getting its own `-32600`/`id: null` entry.

FAILs `ACP-BATCH-209` (elements processed, array reply) and, because it wrote an array,
`ACP-TRANSPORT-001` (MANDATORY) -- so the run is NOT CONFORMANT.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersBatchWithArrayAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._collector: list[dict[str, Any]] | None = None  # non-None while dispatching an array

    def _handle_batch(self, items: list[Any]) -> None:
        if not items:
            super()._handle_batch(items)
            return
        self._collector = []
        for item in items:
            if (
                not isinstance(item, dict)
                or item.get("jsonrpc") != "2.0"
                or not isinstance(item.get("method"), str)
            ):
                self._write(
                    {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
                )
            else:
                self._handle(item)
        responses, self._collector = self._collector, None
        if responses:
            self._write_line(responses)

    def _write(self, obj: dict[str, Any]) -> None:
        # Replies to the array's own entries are collected; agent-originated messages (`method`)
        # still stream out immediately.
        if self._collector is not None and "method" not in obj:
            self._collector.append(obj)
            return
        super()._write(obj)


def main() -> None:
    AnswersBatchWithArrayAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
