# v2 client metadata checks

The regular `acp-tck` command drives an agent. It cannot inspect a real client's
stored metadata, so observing valid patches there does not prove that a client
retains untouched keys. This separate, opt-in runner checks the state exposed by
a client test adapter:

```bash
uv run python -m tck.v2.client_metadata \
  --entity tool_call_update --entity terminal_update \
  --report-json client-metadata.json -- /path/to/client-adapter
```

The adapter must decode the supplied message and invoke the implementation's
actual update path, then return its stored metadata. Do not implement a second
metadata reducer in the adapter: a passing result would only test that copy.
State which client/SDK revision and update path the adapter exercises when
sharing results. The repository's fixture adapter is only a runner self-test,
not an SDK implementation or evidence of client conformance.

## Adapter contract

The runner launches a fresh subprocess for each entity/case. Its stdin/stdout
carry one JSON-RPC 2.0 object per line; log to stderr. The runner does not perform
an ACP `initialize` handshake: these two methods are a test-only control surface,
not new ACP methods a production client must implement.

1. `_tck/reset` with `{"protocolVersion":2,"entity":"tool_call_update"}` prepares
   an empty session named `tck-metadata-session`. Return an empty result object.
2. `_tck/apply` with `{"message": <ACP message>}` delivers one complete
   `session/update` notification. Apply it through the client's normal decoding
   and storage path. Await completion before responding, and return
   `{"_meta": <stored entity metadata>}` with no other result fields. Return
   JSON `null` or `{}` when no metadata remains; these are equivalent.

The methods are sequential requests with integer ids. Reply using the received
id and `"jsonrpc":"2.0"`. Return a JSON-RPC error if the requested entity/path
is unsupported; do not silently accept it. Close on stdin EOF. A rejected
request, process failure, timeout, malformed snapshot or mismatched state makes
that case FAIL. `--timeout` sets the per-response timeout in seconds (default 5).

Every notification uses the same entity identity within its case. Its
`params._meta` contains an unrelated marker which must not enter entity state.
The inner `params.update._meta` is the metadata patch. A tool-call notification
looks like this (the `_tck/apply` wrapper is omitted):

```json
{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"tck-metadata-session","_meta":{"tck.example/notification":"do not retain"},"update":{"sessionUpdate":"tool_call_update","toolCallId":"entity-1","title":"Metadata test","_meta":{"a":3}}}}
```

Select each supported entity explicitly with `--entity` (repeatable):
`tool_call_update`, `terminal_update`, `user_message`, `agent_message`,
`agent_thought`, `session_info_update`, `compaction_update`, `subagent_update`,
or `session_message`. No unselected entity is checked. The last two variants are
draft-only. This runner currently covers notification upserts, not permission
request subjects, chunks, content-item metadata, intermediary coalescing, or
cross-entity/session isolation.

## Cases and results

Expected states are literal examples of the pinned
[metadata patch rule](https://github.com/agentclientprotocol/agent-client-protocol/blob/beac4ba96190018e9f6d82e148ff275084c5aa3e/docs/protocol/v2/draft/extensibility.mdx#metadata-patches)
and [RFD conformance cases](https://github.com/agentclientprotocol/agent-client-protocol/blob/beac4ba96190018e9f6d82e148ff275084c5aa3e/docs/rfds/v2/meta-patches.mdx#conformance-cases).
The runner contains no reducer for computing expected state. It checks each
intermediate snapshot, including:

- Initial omission, clear, empty object and null-valued key removal.
- Omission and `{}` retaining previous metadata; `null` clearing it.
- `{a:1,b:2}` followed by `{a:3}` retaining `b`, and `{a:null}` removing `a`.
- Nested objects/arrays replacing whole values, with nested nulls kept as data.
- Unknown keys, removal of the last key, clear then object, and replay with
  explicit removals over stale metadata in receive order.

Exit code 0 means every selected entity/case passed through that adapter;
1 means at least one failed; 2 means invalid command usage. Optional
`--report-json` writes the selected entities, pinned specification link,
per-case results and `passed` flag. This is a scoped client-state result,
separate from the regular TCK requirement registry and agent conformance verdict.
No third-party client adapter is bundled or validated by these self-tests.
