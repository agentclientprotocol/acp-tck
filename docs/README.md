# Contributor docs

Contracts for working on the TCK. Operator docs (running the TCK, options, reading a report) are in the
[top-level README](../README.md); the repo layout, commands and conventions are in
[`AGENTS.md`](../AGENTS.md).

- [`requirements.md`](requirements.md) -- requirement ids and their lifecycle, tiers, statuses and the verdict,
  citation rules, and the ledger of deliberate non-requirements.
- [`writing-tests.md`](writing-tests.md) -- adding a requirement and its test, markers, probes, the error-code
  policy, SKIP vs FAIL, and fixture agents.
- [`mock-client.md`](mock-client.md) -- the `run_prompt` contract: turn end in v1 and v2, permission policies,
  background-work permission requests, and cancel races.
- [`harness.md`](harness.md) -- the raw stdio client API (`tck.common.harness`).
- [`spec-updates.md`](spec-updates.md) -- how to update the TCK to a new spec revision, including the final
  id-alignment step and the cross-check refresh.
