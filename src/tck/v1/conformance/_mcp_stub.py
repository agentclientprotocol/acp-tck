"""A minimal stdio MCP server used by ACP-SESSION-003/004, run as a standalone script:

    python _mcp_stub.py <marker-path>

Speaks just enough newline-delimited JSON-RPC to complete an MCP handshake: answers
`initialize` (echoing the requested `protocolVersion`), `ping`, and `tools/list` (no tools), and
`-32601` to any other request. Notifications are ignored. On the first `initialize` it writes
`<marker-path>`, which is how the TCK observes that the agent actually connected. Exits on
stdin EOF. Pure stdlib, and not imported by the test suite.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_FALLBACK_MCP_VERSION = "2025-06-18"


def _reply(msg_id: object, result: dict) -> None:
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}) + "\n")
    sys.stdout.flush()


def main() -> None:
    marker = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    for line in sys.stdin:
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict) or "id" not in msg or "method" not in msg:
            continue
        method = msg["method"]
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        if method == "initialize":
            if marker is not None and not marker.exists():
                marker.write_text("initialize\n")
            _reply(
                msg["id"],
                {
                    "protocolVersion": params.get("protocolVersion") or _FALLBACK_MCP_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "acp-tck-stub", "version": "0.0.0"},
                },
            )
        elif method == "ping":
            _reply(msg["id"], {})
        elif method == "tools/list":
            _reply(msg["id"], {"tools": []})
        else:
            error = {"code": -32601, "message": "Method not found"}
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "error": error}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
