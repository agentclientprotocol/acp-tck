# What would it take to address the PR #10 follow-up "Six MCP ledger reasons still rest on 'the TCK doesn't host an MCP server'", and how complex is it?

**Sources checked:** acp-tck @ `f5d3aa3` (branch `pr10-follow-ups`); agent-client-protocol checkout at HEAD
`94d7666d`, every spec line read at the TCK pin `3961af94fa62d2386d993cadf1afc8b146fc799a` (`git show 3961af94:<path>`);
PR #10 body (`gh pr view 10`). The Rust and Python SDKs were not consulted: the question is about TCK scope, and no
row below depends on runtime behaviour the spec leaves open.
**Confidence:** high for the inventory, the spec text and scope (a). Medium for the scope (b) LOC estimates and test
designs, which are sketches I have not built.

## Answer

The PR does not list the six entries. By matching its wording I identify seven MCP ledger entries whose `reason`
depends on what the TCK's own MCP server does or does not do: v1 `:127`, and v2 `:267`, `:363`, `:445`, `:450`,
`:465`, `:521` (all in `spec-tracker/maps/v*.toml`). Six of them say the TCK "does not host", "cannot feed" or "only
records". The seventh (v2 `:445`) rests mostly on negative evidence, but it also blames the stub. Two of the six
reasons are also **factually wrong**: the TCK already ships a stdio MCP stub (`src/tck/v{1,2}/conformance/_mcp_stub.py`,
used by v1 ACP-SESSION-003/004/006 and v2 ACP-SESSION-006).

**Scope (a) is legitimate and small.** `docs/requirements.md:154-156` explicitly allows an entry "marked 'Deferred'
that names the real blocker". The repo already uses that form, e.g. `spec-tracker/maps/v1.toml:399` ("Deferred: the
mock client implements no `terminal` capability... It would be unblocked by a mock client that...") and
`v2.toml:191` ("observable but not yet built"). Scope (a) rewords seven `reason` strings in two TOML files, about
20 changed lines and no code. Size **S**.

**Scope (b) is not one thing.** It splits by stub type:
- **stdio-only (b1), M.** Extend the existing stdio stub to record its `initialize` params, cwd, `ACP_TCK_*` env and
  each launch. That makes four v2 rules testable (cwd/env, the elicitation capability, the resume complete set),
  about 600-900 LOC.
- **HTTP (b2), M to L.** A new in-process HTTP MCP stub, for headers-origin in v1 and v2 and transport-owned headers
  in v2, about 700-1000 LOC.
- **Tool output (b3), blocked on design.** The two forwarding rules need the agent's model to call a stub tool. No
  prompt can force that, so they need a prompt-option design, like the `--subagent-prompt` follow-up.
- **`acp` transport (b4).** Part of the MCP-over-ACP Active RFD's untested remainder. Leave it out.

All of (b) together is **L** (1500-2500 LOC) and does not fit "one PR alongside a few other small/medium follow-ups".
Recommendation: do (a) for all seven in this PR. Optionally add b1's elicitation and cwd/env rows if the PR has room.
Defer b2 and b3.

## Requirements

The seven ledger entries, with the spec tier each would carry if it became a row:

| # | Ledger entry | Rule (spec text at pin) | Tier if made a row | Citation |
|---|---|---|---|---|
| 1 | v1 `spec-tracker/maps/v1.toml:124-127` | Agents SHOULD send `headers` only to the configured origin | SHOULD → ADVISORY, SKIP gate `agentCapabilities.mcpCapabilities.http` | spec `docs/protocol/v1/draft/session-setup.mdx:661` |
| 2 | v2 `spec-tracker/maps/v2.toml:264-267` | "Keys and prefixes that MCP reserves keep their MCP meaning, and Agents preserve them when forwarding MCP content" (no keyword) | descriptive → ADVISORY or INFORMATIONAL (tier decision); behaviour-gated (a forwarded tool result) | spec `docs/protocol/v2/draft/extensibility.mdx:102` |
| 3 | v2 `spec-tracker/maps/v2.toml:360-363` | An Agent that forwards elicitation for an MCP server MUST NOT copy the Client's capability object unchanged. It advertises each supported mode explicitly, and omits MCP `elicitation` when the Client advertises no modes | MUST in draft docs, but conditional on forwarding → CAPABILITY with an `inferred:` gate (e.g. `inferred:mcpElicitationForwarding`), per `docs/requirements.md:63-80` | spec `docs/protocol/v2/draft/elicitation.mdx:54`; semantics of "no modes" `:42-48` |
| 4 | v2 `spec-tracker/maps/v2.toml:442-445` (7th, see Discrepancies) | On `session/resume` and `session/fork`, `mcpServers` is the complete set. Agents SHOULD NOT restore servers from earlier requests | SHOULD NOT → ADVISORY, gate `capabilities.session` (resume is baseline once advertised, see v2 ACP-RESUME-001 `src/tck/v2/requirements.py:1686-1696`) | spec `docs/protocol/v2/draft/session-setup.mdx:549`; related `:53` (resume of an active session: "the request's MCP servers ... replace the previous ones") |
| 5 | v2 `spec-tracker/maps/v2.toml:447-450` | SHOULD launch stdio servers with the session `cwd`. `env` entries are added to the inherited environment and the last duplicate wins (Agents MAY reject duplicates with `-32602`). For transport-owned headers (`Accept`, `MCP-Protocol-Version`) "Agents use the transport's values" | cwd: SHOULD → ADVISORY, gate `capabilities.session.mcp.stdio`. env/last-wins and owned headers: no keyword → ADVISORY (precedent: unkeyworded `-32602` rule ACP-MCP-204 is ADVISORY) | spec `docs/protocol/v2/draft/session-setup.mdx:607,626` |
| 6 | v2 `spec-tracker/maps/v2.toml:463-466` | same as #1 | ADVISORY, gate `capabilities.session.mcp.http` | spec `docs/protocol/v2/draft/session-setup.mdx:696` |
| 7 | v2 `spec-tracker/maps/v2.toml:518-521` | ACP `ContentBlock` is a superset of MCP's, so Agents *can* forward MCP tool output unchanged (permissive). A content type from a later MCP revision "isn't forwarded as is. Agents convert it ... or omit it" (no keyword) | `:18` is a MAY and does not belong in the ledger as a rule. `:20` is descriptive → ADVISORY/INFORMATIONAL, behaviour-gated | spec `docs/protocol/v2/draft/content.mdx:18,20` |

v1 has no counterpart of #2, #3, #4, #5 or #7. I checked v1 `session-setup.mdx` (no cwd/env/restore text; `:645-662`
holds only the security bullets), v1 `elicitation.mdx:54-55` (no forwarding rule) and v1 `content.mdx:18`
(permissive only). So under Rule B (`docs/requirements.md:13-24`) only #1/#6 could share an id across versions.

## Details

### Current state of the TCK

- **stdio stub exists:** `src/tck/v2/conformance/_mcp_stub.py:1-61` (v1 copy is identical except the docstring,
  `src/tck/v1/conformance/_mcp_stub.py:1`). It answers `initialize`/`ping`/`tools/list` (with no tools) and returns
  `-32601` for everything else. On the first `initialize` it writes `{"argv": [...]}` to a marker path, only if the
  marker does not exist yet, so it records only the first launch.
- **v2 use:** `src/tck/v2/conformance/test_session_capabilities.py:1848-1957` (`_drive_and_scan_for_canary`, with a
  `_STUB_GRACE_SECONDS = 3.0` wait for the marker). v1 use: `src/tck/v1/conformance/test_session.py:71-182`
  (ACP-SESSION-003 MANDATORY, 004 ADVISORY "SHOULD connect", 006).
- **HTTP:** no HTTP server anywhere. The http probes use `http://127.0.0.1:1/tck-nonexistent`
  (`test_session_capabilities.py:1756,1953`).
- **`acp` transport:** only negative probes (ACP-MCP-203 `:1779-1821`; `mcp/message` probes in `test_jsonrpc.py:134`
  and `test_extensibility.py:291`).
- **Session setup with MCP servers:** v2 `new_session` omits `mcpServers` (`_helpers.py:227-229`). `resume_session`
  takes `mcp_servers=` (`_helpers.py:253-283`). `connected_agent(..., capabilities=...)` overrides client
  capabilities (`_helpers.py:84-88`).
- **Mock client:** advertises no elicitation and answers `elicitation/create` with `-32601` (`docs/mock-client.md:11-13`).
  ACP-CLIENTCAP-003 relies on `capabilities: {}` (`src/tck/v2/requirements.py:1133-1144`,
  `test_client_capabilities.py:1-8`).
- **Fixtures:** both `_base.py` launch stdio servers with merged env but no `cwd=`. They send MCP `initialize` with
  `capabilities: {}` (`tests/fixtures/agents/v2/_base.py:530-565`; v1 `_base.py:402-435`). Only
  `tests/fixtures/agents/v2/conforming_full.py:56` advertises `mcp: {stdio, http}`.
- **Fixture expectations:** `tests/v{1,2}/test_cli.py` (e.g. v2 `:5202-5207`, v1 `:1537-1541`).

### Scope (a): reword the reasons (no code)

Proposed `reason` text for each entry. It follows the Deferred pattern (`v1.toml:399`, `v2.toml:191`) and drops the
inaccurate "the TCK does not host an MCP server":

1. **v1 `:127` and v2 `:465` (headers origin):** "Deferred: needs an HTTP MCP test server, which the TCK does not
   have yet (its MCP stub is stdio-only), that answers with a cross-origin redirect and records whether the configured
   `headers` reach the second origin. Applies only when the agent advertises `mcpCapabilities.http`
   [v2: `session.mcp.http`]. An agent whose HTTP client never follows the redirect would PASS vacuously."
2. **v2 `:267` (`_meta` keys) and v2 `:521` (tool output):** "Deferred: needs the agent's model to call a tool on a
   TCK-supplied MCP server, and the agent to relay the tool's content in a tool call. No prompt can force either. The
   TCK's stdio stub also exposes no tools." (Wire shape stays covered by schema validation, as `:521` says now.) This
   matches the existing "an agent cannot be made to elicit" entries (`v2.toml:373`).
3. **v2 `:363` (elicitation capability):** "Deferred: observable once the stdio stub records the `capabilities` of
   the MCP `initialize` it receives and the mock client advertises an elicitation mode (it advertises none and would
   then have to answer `elicitation/create`). Not yet built." The section comment at `v2.toml:358` ("coverage
   deferred: the TCK never advertises an elicitation mode") states a TCK choice too. Rewording it is in scope if the
   orchestrator wants it.
4. **v2 `:450` (cwd/env/owned headers):** "Deferred: the stdio stub could record its working directory and the
   `ACP_TCK_*` environment it was launched with, but does not yet. The owned-headers half needs an HTTP test server
   (see `:696`). Whether the base environment is the one 'the Agent would otherwise give the process' is internal to
   the agent."
5. **v2 `:445` (resume/fork complete set):** "Deferred: a relaunch of a server from an earlier request after
   `session/resume` with `mcpServers: []` would be positive evidence, if the stub logged every launch (it records
   only the first). Absence is only negative evidence, and `session/fork` may reuse the source session's connection
   without a new launch."

Files: `spec-tracker/maps/v1.toml`, `spec-tracker/maps/v2.toml` only. Verify with the spec-tracker tests (the
`spec_map.py` loader accepts any `reason` text, `spec-tracker/src/spec_tracker/spec_map.py:88-93`; no lint checks
reason wording).

### Scope (b): sketch

**b0. Stub upgrade, per version.** v1 and v2 never import each other, so each version keeps its own stub copy.
- On every `initialize`, append one JSON line to the marker (append mode, so relaunches are visible) with:
  - `argv`;
  - `cwd` (`os.getcwd()`);
  - `env`: only names starting with `ACP_TCK_`. Never dump the whole environment: it would put the user's secrets in
    marker files and in failure messages;
  - `initialize`: the request `params`, which carries MCP `capabilities`.
- On stdin EOF, append an `eof` record.
- Update ACP-SESSION-006's reader (`test_session_capabilities.py:1913-1918`, v1 `test_session.py`) to the
  line-per-launch format.
- About 40 LOC per stub and 20 per reader.

**b1. stdio-only v2 rows.** Ids are provisional; the spec-update id-alignment rules apply.

- **Launch cwd and env (rule #5), ADVISORY, gate `capabilities.session.mcp.stdio`.** `session/new` with the stub,
  then one prompt turn for lazy agents, as in v1 ACP-SESSION-004.
  - Check that the recorded `cwd` equals `tmp_path` after `realpath`: macOS `/var` vs `/private/var`.
  - Check that `ACP_TCK_A=x` is present.
  - Check that a duplicate `ACP_TCK_DUP` (values `first`, `last`) arrives as `last`. A `-32602` on `session/new` is
    allowed by the MAY and SKIPs the last-wins half.
  - Split cwd and env into two rows, because they have different keywords.
- **Elicitation capability not copied (rule #3), CAPABILITY, `inferred:` gate.** Two connections:
  - Connection A advertises `capabilities.elicitation = {"form": {}, "url": null}`. If the stub's MCP `initialize`
    has no `elicitation`, SKIP (no evidence the agent forwards elicitation). Otherwise FAIL if it deep-equals the
    client object (including `"url": null`), lacks a non-null `form`, or carries a non-null `url`.
  - Connection B advertises `{"form": null, "url": null}`. Run it only if A showed forwarding. FAIL if MCP
    `initialize` has any `elicitation`.
  - Needs a mock-client change. Once a mode is advertised, `run_prompt` must answer `elicitation/create` with a
    schema-valid `decline`/`cancel` (`$defs/CreateElicitationResponse`) instead of `-32601`, so the TCK does not
    break the client contract it advertised. Update `docs/mock-client.md:11-13` too.
  - If the test avoids prompt turns entirely (session/new plus a grace period), the mock-client change can be skipped.
    Agents that connect lazily then SKIP. That is a design choice.
- **No server restore on resume (rule #4), ADVISORY, gate `capabilities.session`.**
  - Create a session with stub A and run one prompt turn.
  - `session/close` it and wait for the stub's `eof` record.
  - `session/resume` with `mcpServers: []`, then run one prompt turn and wait a grace period.
  - FAIL if stub A logged a new launch after the resume; PASS otherwise.
  - Use the create-then-close route from ACP-RESUME-001. Do not use fork: a fork may share the source's live
    connection.
- **Optional adjacent row:** v2 has no counterpart of v1 ACP-SESSION-004 ("SHOULD connect to all MCP servers",
  v2 `session-setup.mdx:685`). ACP-MCP-201 only records it (`src/tck/v2/requirements.py:2535-2550`). With the
  stub, it would be a direct port that shares the id ACP-SESSION-004.
- **Fixtures:**
  - `tests/fixtures/agents/v2/_base.py:530-565` adds `cwd=` from the session's `cwd`. Last-wins is already true
    through dict update.
  - Its MCP `initialize` `capabilities: {}` already satisfies rule #3.
  - Add a relaunch-tracking path for resume.
  - New defect fixtures: `mcp_launch_wrong_cwd.py`, `mcp_env_first_wins.py`, `copies_elicitation_capability.py`,
    `restores_mcp_servers_on_resume.py`.
- **Other files:**
  - `tests/v2/test_cli.py` id sets and defect assertions;
  - `src/tck/v2/requirements.py` rows;
  - ledger: delete `v2.toml:363`, and `:445`/`:450` (or narrow `:450` to the owned-headers half);
  - test module docstring in `test_session_capabilities.py:1-22`.
- **Estimate:** rows about 80 LOC, tests 250-350, stub/readers 60, fixtures 150-250, `test_cli.py` 80-120, mock
  client plus docs 40-80. **Total about 600-900 LOC, M.**

**b2. HTTP MCP stub (rules #1, #6, and the owned-headers half of #5).**
- An in-process asyncio HTTP/1.1 server on `127.0.0.1:0`, run in the test's event loop with stdlib only. It speaks
  minimal Streamable HTTP:
  - POST with a JSON-RPC body returns `application/json`, for `initialize` (echoing the version), `ping` and
    `tools/list`;
  - GET returns 405 and DELETE returns 200;
  - `/.well-known/*` returns 404, so OAuth discovery fails cleanly;
  - it records request headers.
- **Origin probe:**
  - Listener A answers the first POST with `307` and `Location:` pointing at listener B. A different port is a
    different origin, which avoids relying on `localhost` resolving.
  - Use canary values in both `Authorization` and a custom `X-Acp-Tck-Canary`. HTTP libraries strip
    `Authorization` on cross-host redirects by default, but not custom headers, so the custom header tests the
    agent's own rule. (That reqwest/httpx strip `Authorization` is my unverified recollection: a hypothesis.)
  - FAIL if any canary reaches B; PASS otherwise. Record whether B was contacted at all, as an INFORMATIONAL property.
- **Owned headers:** the client config supplies `Accept: text/plain` and `MCP-Protocol-Version: 1999-01-01`.
  - FAIL if the stub sees exactly the client's `Accept` (Streamable HTTP needs `application/json` and
    `text/event-stream`).
  - FAIL if a post-initialize request carries `1999-01-01`.
- **Rows:** v1 and v2 share one headers-origin id (Rule B), plus one v2-only owned-headers row.
- **Placement:** the server is MCP, not ACP, so `src/tck/common/` is a candidate. The alternative is one copy per
  version. That is a design decision.
- **Fixtures:** both `_base.py` need a stdlib (`http.client`) HTTP MCP client that follows or refuses redirects. v1
  fixtures must advertise `mcpCapabilities.http` in some variant. Defect fixtures: `follows_redirect_with_headers`,
  `overrides_owned_headers`.
- **Estimate: about 700-1000 LOC, M to L.** Most of the risk comes from real-agent HTTP clients behaving in different
  ways.

**b3. Tool-output rows (rules #2, #7).**
- The stub exposes one tool returning content that carries:
  - an MCP-reserved `_meta` key, e.g. `io.modelcontextprotocol/...`. The exact MCP reserved-prefix rule was not
    checked: a hypothesis to verify against the MCP spec;
  - an unknown future content type.
- The TCK prompts the agent to call it, and the rows SKIP unless a `tool_call`/`tool_call_update` relays that
  content.
- Blocked on a prompt-option design shared with `--subagent-prompt` (PR #10 "Known limitations").
- INFORMATIONAL or ADVISORY. Not recommended for this PR.

**b4. `acp` transport stub** (TCK serves MCP over `mcp/connect`/`mcp/message`). This means testing the rest of the
MCP-over-ACP RFD, which is Active (`docs/docs.json:211-215` at pin) and of which PR #10 covered only the first part.
It needs that RFD audited first. Out of scope.

## Testability notes

- **#5 cwd/env:** fully observable and deterministic through the stub's own record. A conforming agent launches the
  stub in `tmp_path` with `ACP_TCK_DUP=last`. A defect launches it in its own cwd or keeps the first value. Agents
  that never launch the stub SKIP (prerequisite, as ACP-SESSION-006 does).
- **#3 elicitation:** observable at MCP `initialize`, with no model involvement. A PASS on connection A cannot be
  told apart from "the agent maps modes correctly", which is fine. The "omit when no modes" half is meaningful only
  for agents shown to forward. An agent that advertises MCP elicitation for its own reasons (not forwarding) cannot
  be told apart from a forwarder. That is why the gate is inferred from connection A, and why the B half could be
  ADVISORY rather than CAPABILITY. A tier decision for the orchestrator.
- **#4 restore:** only positive evidence is decisive (a relaunch). PASS is bounded by the grace period and the
  prompt turn. Agents that keep stub processes alive across `session/close` (pooling) would show no relaunch and
  PASS, even though they would be using the old server. That is unobservable without an MCP request to the stub
  during the turn.
- **#1/#6 origin:** FAIL is decisive. PASS is vacuous when the agent's HTTP client does not follow redirects. Not
  testable when the agent is sandboxed from localhost.
- **#2/#7:** model-driven. The rows SKIP against most real agents unless a prompt option exists.
- **Environment limits:** stdio stubs use `sys.executable` plus a path on the TCK host, and HTTP uses `127.0.0.1`. An
  agent run inside a container (`acp-tck -- docker run ...`) can reach neither. This risk already exists for v1
  ACP-SESSION-003 (MANDATORY); new rows only add to it.

## Discrepancies

- **PR text vs ledger:** the PR says "six", but seven entries cite the stub or its absence. v2 `:445` is the borderline
  one: it rests mainly on negative evidence, which is a legitimate non-TCK reason, but it names the stub as well.
- **Ledger vs code:**
  - "which the TCK does not host" (v1 `:127`, v2 `:267`, `:465`) is accurate only for HTTP and tools. The TCK does
    host a stdio MCP stub.
  - v2 `:450` "records only the `argv`" is a limit of the TCK's own stub. That is a TCK choice, which
    `docs/requirements.md:154` forbids as a reason.
- **Ledger statement vs spec keyword:**
  - The v2 `:450` statement groups the unkeyworded "Agents use the transport's values" (`session-setup.mdx:626`) and
    "last entry wins" (`:607`) under SHOULD.
  - The v2 `:521` statement treats the permissive `content.mdx:18` ("can forward") as a rule. Per
    `docs/requirements.md:150-151`, pure MAYs stay out of the ledger, so only `:20` belongs there.
- **Spec vs schema vs SDKs:** no conflict found. SDKs not checked.

## Open questions

1. **Which "six" the PR meant.** Confirm whether v2 `:445` is in or out. Recommendation: reword all seven anyway.
2. **Tiers** for the unkeyworded rules (#2, #5 env/owned headers, #7): ADVISORY vs INFORMATIONAL. **Gate** for #3:
   CAPABILITY `inferred:` vs ADVISORY.
3. **Elicitation test design:** should the mock client advertise an elicitation mode and answer `elicitation/create`
   (a mock-client contract change), or should #3 avoid prompt turns and SKIP lazy-connecting agents?
4. **HTTP stub placement:** `src/tck/common/` (MCP is version-agnostic) or a per-version copy. Also, whether the TCK
   may open listening sockets at all (firewall prompts on macOS for `127.0.0.1` are usually absent, but CI sandboxes
   vary).
5. **Missing v2 row:** v2 has no ACP-SESSION-004 counterpart ("SHOULD connect to all MCP servers",
   `session-setup.mdx:685`). It is neither a row nor a ledger entry. This is a coverage gap; route it with b1 or
   separately.
6. **MCP reserved `_meta` prefix rule** and the 2026-07-28 MCP `ContentBlock` set. Needed only for b3; check against
   the MCP spec, not ACP.
7. **New related rule:** the related rule `session-setup.mdx:53` (resuming an active session replaces its MCP
   servers) is not in the registry or the ledger. A spec-update researcher should classify it.
