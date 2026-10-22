# Vendored files

`schema.unstable.json` and `meta.unstable.json` in this directory are verbatim copies of the ACP
v1 JSON Schema, vendored from the spec's source-of-truth repository. Do not hand-edit them.

**v1 verifies entirely against the draft (unstable) schema.** The upstream repo publishes both a
stable `schema.json`/`meta.json` and a superset `schema.unstable.json`/`meta.unstable.json` that
additionally defines fields and methods still gated behind an individual RFD. Those extras are
optional for agents, but any an agent uses are validated against their draft shapes. The stable
files are deliberately not vendored. The upstream file names are kept as-is.

- **Source repo:** https://github.com/agentclientprotocol/agent-client-protocol
  (local read-only checkout used for the copy: the path configured by the
  `check-specification` skill, `.agents/skills/check-specification/.repo`)
- **Commit:** `beac4ba96190018e9f6d82e148ff275084c5aa3e`
- **Date vendored:** 2026-10-19
- **Copy commands used:**

  ```
  cp <spec-repo>/schema/v1/schema.unstable.json src/tck/v1/schema/schema.unstable.json
  cp <spec-repo>/schema/v1/meta.unstable.json   src/tck/v1/schema/meta.unstable.json
  ```

## Refreshing

1. Confirm the spec repo checkout's current HEAD: `git -C <spec-repo> rev-parse HEAD`.
   Before step 3 bumps the pin, run `uv run python scripts/spec-impact.py <pinned> <new> --version v1 --fix`
   to remap the doc line citations.
2. Re-run the two `cp` commands above with the new checkout path.
3. Update the commit hash and date in this file, and `SCHEMA_REVISION` in
   `src/tck/v1/protocol.py`.
4. Re-run `uv run pytest` -- `tests/v1/test_validation.py` will catch any shape the new schema
   changed that `src/tck/v1/protocol.py` / `src/tck/v1/validation.py` assumed.
5. If method names, `x-side`/`x-method` annotations, or the top-level `anyOf` branch layout
   (`Agent` / `Client` / `ProtocolLevel`) changed shape, re-check `src/tck/v1/protocol.py` and
   `src/tck/v1/validation.py` by hand -- both parse the schema structurally, not just by value.
   Note that a wire method can appear under both `agentMethods` and `clientMethods` with a
   different kind per direction (`mcp/message`: an agent -> client request, a client -> agent
   notification).
6. Citations into the schema are JSON-Pointer name paths (`schema.unstable.json#/$defs/...`);
   `tests/v1/test_registry.py` fails if a refresh renames or removes one, so fix those citations.
   Prose citations point at the draft doc tree (`docs/protocol/v1/draft/*.mdx`) by line number,
   pinned to the same commit -- re-check them whenever the commit moves.
