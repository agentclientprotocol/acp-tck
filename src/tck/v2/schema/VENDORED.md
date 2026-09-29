# Vendored files

`schema.unstable.json` and `meta.unstable.json` in this directory are verbatim copies of the ACP
v2 JSON Schema, vendored from the spec's source-of-truth repository. Do not hand-edit them.

**v2 is Draft** (schema version `2.0.0-alpha.5` as of the commit below) -- unlike `tck/v1/schema/`,
this directory should be expected to churn: field shapes, capability markers, and even method
inventories may still change upstream before v2 stabilizes.

**v2 verifies entirely against the draft (unstable) schema.** The upstream repo publishes both a
stable `schema.json`/`meta.json` and a superset `schema.unstable.json`/`meta.unstable.json` that
additionally defines fields and methods still gated behind an individual RFD (e.g.
`AgentCapabilities.providers`, `SessionCapabilities.fork`, `providers/*`, `mcp/message`). Because
v2 itself is still Draft, agents are expected to implement those RFDs, so the TCK uses the
superset for everything: method tables, full jsonschema validation (`ACP-SCHEMA-001`), and the
unknown-root-key check. The stable files are deliberately not vendored. The upstream file names
are kept as-is.

- **Source repo:** https://github.com/agentclientprotocol/agent-client-protocol
  (local read-only checkout used for the copy: the path configured by the
  `check-specification` skill, `.agents/skills/check-specification/.repo`)
- **Commit:** `9af0e9f748db9f4cc4c410a7b212ead4f98ae78c`
- **Date vendored:** 2026-09-29
- **Copy commands used:**

  ```
  cp <spec-repo>/schema/v2/schema.unstable.json src/tck/v2/schema/schema.unstable.json
  cp <spec-repo>/schema/v2/meta.unstable.json   src/tck/v2/schema/meta.unstable.json
  ```

## Refreshing

1. Confirm the spec repo checkout's current HEAD: `git -C <spec-repo> rev-parse HEAD`.
2. Re-run the two `cp` commands above with the new checkout path.
3. Update the commit hash and date in this file, and `SCHEMA_REVISION` in
   `src/tck/v2/protocol.py`.
4. Re-run `uv run pytest` -- `tests/v2/test_validation.py` will catch any shape the new schema
   changed that `src/tck/v2/protocol.py` / `src/tck/v2/validation.py` assumed.
5. If method names, `x-side`/`x-method` annotations, the top-level `anyOf` branch layout (`Agent`
   / `Client` / `AgentBatchCall` / `AgentBatchResponse` / `ClientBatchCall` / `ClientBatchResponse`
   / `ProtocolLevel`), or the open-enum `"other"` fallback branch shape (e.g. `StopReason`)
   changed, re-check `src/tck/v2/protocol.py` and `src/tck/v2/validation.py` by hand -- both parse
   the schema structurally, not just by value.
