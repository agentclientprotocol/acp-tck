# Harness API (`tck.common.harness`)

A raw, hand-rolled asyncio NDJSON stdio client. It is deliberately not built on the ACP Python SDK, whose typed
layer cannot emit malformed traffic and whose transport silently drops non-conforming lines. The harness never
drops or crashes on anything the agent sends; it records it.

It is version-agnostic and shared by the v1 and v2 suites. The mock-client driver built on top of it is described
in [mock-client.md](mock-client.md).

## `AgentLaunch`

`AgentLaunch(command, cwd=None, env_overrides={}, startup_timeout=5.0, default_timeout=5.0,
max_line_bytes=64*1024*1024, close_grace=2.0)`

- `env_overrides` is applied on top of the inherited environment.
- `startup_timeout` is the deadline callers use for the first read after spawn; the class does not enforce it.
- `default_timeout` is the per-read deadline when a call omits `timeout`, and the deadline for a write's drain.
- `max_line_bytes` is the stream buffer limit. It is generous on purpose, so hitting it is itself informative.
- `close_grace` is passed to `close()` on teardown.

## `AgentProcess(launch)`

An async context manager. The child runs in its own process group on POSIX so `close()` can terminate the whole
group, including agents started through wrapper scripts.

- **Sending:** `send_raw` / `send_message` / `send_request(method, params=None, *, id=None) -> id` /
  `send_notification`. `send_request` returns the id it used: an auto-incrementing int unless one is given
  (which may be a string).
- **Reading:** `read_line(timeout=None) -> TranscriptEntry` returns the next stdout line, byte-lossless even past
  `max_line_bytes` (it sets `oversize` rather than truncating). It raises `AgentTimeout` or `AgentExited`; both
  carry the transcript so far, and `AgentExited` also carries stderr and the exit code.
- **Waiting:** `wait_for_response(id, timeout=None)` and `wait_for_message(predicate, timeout=None)` read until a
  match. Lines read on the way stay in a buffer that `pending()` drains and returns, so nothing is lost.
- **Observing:** `transcript` is everything sent and received, in both directions, malformed lines included.
  `stderr_text()` returns the agent's stderr so far.
- **Closing:** `close(grace=2.0)` runs the ladder stdin close, then SIGTERM, then SIGKILL, with each rung capped at
  `grace` and skipped once the process has exited. It drains stdout at each stage so late output is still
  captured.

## `TranscriptEntry`

`direction` (`Direction.SENT` or `RECEIVED`), `raw`, `timestamp` (monotonic), `text` / `text_error`, `parsed` /
`parse_error`, `oversize`. Decode and parse failures are recorded as fields and never raised.
`matches_id(id)` is true for a JSON-RPC response (an `id`, no `method`) to that id.
