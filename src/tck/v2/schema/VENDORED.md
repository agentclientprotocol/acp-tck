# Vendored files

`schema.unstable.json` and `meta.unstable.json` in this directory are verbatim copies of the ACP
v2 JSON Schema, vendored from the spec's source-of-truth repository. Do not hand-edit them.

**v2 is Draft** (schema version `2.0.0-alpha.9` as of the commit below) -- unlike v1, where
only RFD-gated additions churn, even v2's core may still change upstream before it stabilizes:
field shapes, capability markers, and even method inventories.

**v2 verifies entirely against the draft (unstable) schema.** The upstream repo publishes both a
stable `schema.json`/`meta.json` and a superset `schema.unstable.json`/`meta.unstable.json` that
additionally defines fields and methods still gated behind an individual RFD. The stable files are
deliberately not vendored. The upstream file names are kept as-is.

- **Source repo:** https://github.com/agentclientprotocol/agent-client-protocol
  (copied from a local clone, `<spec-repo>` below)
- **Commit:** `beac4ba96190018e9f6d82e148ff275084c5aa3e`
- **Date vendored:** 2026-10-19
- **Copy commands used:**

  ```
  cp <spec-repo>/schema/v2/schema.unstable.json src/tck/v2/schema/schema.unstable.json
  cp <spec-repo>/schema/v2/meta.unstable.json   src/tck/v2/schema/meta.unstable.json
  ```

## Refreshing

1. Confirm the spec repo checkout's current HEAD: `git -C <spec-repo> rev-parse HEAD`.
   Before step 3 bumps the pin, run `uv run --package spec-tracker spec-impact <pinned> <new> --version v2 --spec-repo <spec-repo> --fix`
   to remap the doc line citations.
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
6. Citations into the schema are JSON-Pointer name paths (`schema.unstable.json#/$defs/...`);
   `tests/v2/test_registry.py` fails if a refresh renames or removes one, so fix those citations.
