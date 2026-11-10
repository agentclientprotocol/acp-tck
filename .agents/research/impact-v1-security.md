# v1 impact: `docs/protocol/v1/draft/security.mdx` (new at target)

**Sources checked:** agent-client-protocol (spec checkout `agent-client-protocol-2`, HEAD = `3961af94fa62d2386d993cadf1afc8b146fc799a`, not pulled per brief); base `beac4ba96190`. TCK repo at branch `eugenethedev/update-spec`. Reference SDKs not consulted (nothing here relies on implicit runtime behavior).
**Confidence:** high. The doc is 74 lines, I read all of it, and no registry row cites it. Every statement is SHOULD/SHOULD NOT/MAY.

## Answer

`security.mdx` is a new page with **zero MUST** statements. Its SHOULD/MAY rules bind Clients (rendering, URIs, links, terminal output, slash commands, intermediaries), Implementations in general (`agentInfo`, `_meta` credentials), Agents (URI handling, prompt injection, multi-user scoping) and Transport authors. No existing registry row cites it, and no existing row's text or tier is affected. The stable page `docs/protocol/v1/security.mdx` is identical apart from link prefixes.

I propose **no new requirements** from this doc. Almost all Agent-directed rules need either model behavior, a real tool run, or a multi-user deployment, none of which a client-driven TCK can observe deterministically. I propose **11 ledger entries** for statements someone might expect the TCK to test. I also flag one cross-doc candidate for the session-setup report: an ADVISORY "agent does not echo MCP `env`/`headers` secrets".

## Summary table

| id | classification | note |
|---|---|---|
| (all existing rows) | unchanged | No registry row cites `security.mdx` (`grep` of `requirements.py`: none). `spec-impact` Appendix A lists "none" for it. |
| ACP-INIT agentInfo row (`requirements.py:185`) | unchanged | `agentInfo` presence/shape. Line 13 adds only a "do not use for security decisions" rule that does not touch presence or shape. |
| ACP-META-001 (`requirements.py:962`) | unchanged | `_meta`/`traceparent` accepted on `session/prompt`. Line 42 ("no credentials in `_meta`") is orthogonal. |
| ACP-SYSPROMPT-001/002/003 | unchanged (by this doc) | Line 51 repeats the system-prompt rule from `session-setup.mdx`, which the session-setup report owns. |
| (new requirements) | none proposed | See "Observable-agent-side analysis". |
| LEDGER-SEC-01 .. LEDGER-SEC-11 | new deliberate non-requirements | See ledger section. |
| Candidate (cross-doc, defer to session-setup report) | new, ADVISORY | Secret-echo check. Cites `session-setup.mdx:654-662`, with `security.mdx:42` as secondary. |

## Normative statement inventory (target line numbers, `docs/protocol/v1/draft/security.mdx`)

Tier column is the spec's wording. "Binds" is who the rule applies to. "Observable?" asks whether a client-driven TCK can see an agent violate it.

| Line | Statement | Wording | Binds | Observable by TCK? |
|---|---|---|---|---|
| 13 | Do not use `clientInfo`/`agentInfo` for security decisions | SHOULD NOT | Any implementation | No (internal decision). |
| 13 | Client identifies Agent from its own launch configuration | SHOULD | Client | No (client-side). The TCK does this: it gets the command from `--tck-agent-cmd` and only records `agentInfo` in the report (`src/tck/common/plugin.py:757-760`). |
| 21 | No scripts from Agent content; disable or sanitize raw HTML in Markdown | SHOULD NOT / SHOULD | Client | No. |
| 22 | No auto-run of active content (diagram renderers etc.) | SHOULD NOT | Client | No. |
| 23 | No opening links without user action; show full target and confirm for non-http(s) schemes | SHOULD NOT / SHOULD | Client | No. |
| 24 | Show full link target when it differs from the text | SHOULD | Client | No. |
| 25 | Reveal or remove bidi, zero-width, and tag characters in commands, paths, URLs, diffs, permission requests | SHOULD | Client | No. |
| 26 | Neutralize terminal control sequences when printing Agent text to a terminal | SHOULD | Client | No. The TCK is itself such a client for the stderr/transcript text it prints (see Open questions). |
| 27 | Keep Agent slash commands distinguishable from Client commands | SHOULD | Client | No. |
| 28 | Bound or throttle permission requests, elicitations, output | MAY | Client | No (optional, client-side). |
| 34 | Render images from `data`; do not fetch remote URIs without user action | SHOULD / SHOULD NOT | Client | No. |
| 35 | Automatic fetches: only `https:`/`data:`, no credentials, refuse loopback and private networks, bound response size | SHOULD (x4) | Client | No. |
| 36 | No scripts in SVG images | SHOULD NOT | Client | No. |
| 37 | No reading a `file:` URI outside the root set without user action | SHOULD NOT | Client | No. |
| 38 | Agents apply root-set and fetch rules to URIs in prompts | SHOULD | Agent | Only partially, and fragile (see below). |
| 42 | No credentials in `_meta` (including `traceparent`, `tracestate`, `baggage`) | SHOULD NOT | Any implementation | Not generally. "Credential" is undefined, and scanning for token-like strings is heuristic. |
| 43 | Session/message/tool-call/terminal IDs are not credentials | statement (no keyword) | n/a | No. |
| 47 | Treat embedded resources, files, tool results, MCP results as data, not user instructions | SHOULD | Agent | No (model behavior, non-deterministic). |
| 48 | Request permission before sending data off the machine after reading untrusted content | SHOULD | Agent | No. Needs a real tool-using turn and an agent-specific trigger. |
| 49 | Request permission before writing files that control execution or approval (VCS hooks, editor or Agent settings, MCP config) | SHOULD | Agent | No, for the same reason. |
| 50 | Client does not open links, run commands, change settings, or send data based only on Agent-authored text | SHOULD NOT | Client | No. |
| 51 | System prompt carries more weight than user turns. Clients send only trusted content at that level; Agents may reject it | SHOULD / MAY | Client / Agent | Rejection is optional (MAY), so it cannot be required. The rejection modes the spec does state as MUST live in `session-setup.mdx:415,418,419,422` and are covered by ACP-SYSPROMPT-002/003. |
| 55 | Clients use only intermediaries the user trusts | SHOULD | Client | No. |
| 56 | Intermediaries do not answer permission requests or elicitations for the user except under user-configured policy | SHOULD NOT | Intermediary | No. The TCK sits at the client position and has no intermediary. |
| 57 | A multi-user Agent scopes `session/list`, load/resume, permission requests, and elicitations to the owning user | SHOULD | Agent | No. It needs distinct user identities, and ACP has no user identity on the wire. |
| 61 | Custom transports document their security considerations, including peer authentication | SHOULD | Transport author | No (documentation). |

Pure prose, skipped: the trust-model bullets without keywords (lines 10-12, 15), the feature guidance links (lines 63-70), and the residual-risk note (line 74).

## Observable-agent-side analysis (why no new requirements)

Candidates considered, one by one.

1. **Line 38, Agents apply root-set and fetch rules to URIs in prompts.**
   - A TCK could send a `resource_link` to a loopback listener it hosts and flag any hit, or to `file:///` outside the root set.
   - Agents are not required to dereference resource links. The turn outcome is model-driven. The hit would be a SHOULD violation only if the agent auto-fetches.
   - A TCK-hosted socket also means the TCK opens network listeners, which is out of project scope.
   - **Recommendation:** ledger (LEDGER-SEC-08). It is not suitable even as INFORMATIONAL, because a quiet agent proves nothing.
2. **Line 42, no credentials in `_meta`.**
   - The TCK could plant a sentinel secret and check it never reappears in agent `_meta`. The only natural place to plant one is the MCP `env`/`headers` fields, and that rule is in `session-setup.mdx:660`.
   - The TCK does not currently send a non-empty `env`: ACP-SESSION-003's stdio entry has `"env": []` (`src/tck/v1/conformance/test_session.py:77`).
   - This is the one realistic observable rule. It belongs to the session-setup report. See "Cross-doc candidate".
3. **Lines 47-49, prompt-injection and permission rules.** These depend on model behavior and tool use. A deterministic fixture cannot establish conformance for a real agent, and a real agent gives non-reproducible results. Ledger (LEDGER-SEC-09/10).
4. **Line 57, multi-user scoping.** No user identity exists in ACP, so no client can test it. Ledger (LEDGER-SEC-11).
5. **Line 51, system prompt MAY reject.** MAY, and already covered where the spec states a MUST. No change.

## Cross-doc candidate (defer to the session-setup/MCP report; do not number it here)

- **Rule:** "Agents SHOULD NOT include `env` or `headers` values in session updates, errors, `_meta`, `session/list` results, replayed history, model context, or command lines, and SHOULD NOT log or persist them." Source: `docs/protocol/v1/draft/session-setup.mdx:660 @ 3961af94fa62`. Secondary: `security.mdx:42`.
- **Tier:** ADVISORY (SHOULD NOT).
- **Observability:** partial.
  - Send `session/new` with the stub stdio MCP server entry, carrying `env: [{name: "TCK_SECRET", value: "<unique sentinel>"}]`.
  - Check that the sentinel never appears in any agent-authored message in the transcript: `session/update`, error `message`/`data`, `session/list` results, and (if `loadSession` is advertised) the `session/load` replay.
  - A pass is weak evidence, because the agent might not log or echo anything in this window. A fail is a clean violation. The agent's stderr and its logs on disk (the "log or persist" half) are out of scope.
- **Suggested fixture:** a variant of `conforming.py` that echoes `env` values into an `agent_message_chunk` or an error `data` field.
- **DECISION NEEDED (orchestrator):** let the session-setup report own the id and tier. I recommend ADVISORY, and I recommend not claiming any "persist/log" coverage.

## Ledger entries (deliberate non-requirements)

Format follows `spec-tracker/maps/v1.toml`. The ledger is currently empty, so check the field names there before adding. Citations are `docs/protocol/v1/draft/security.mdx:<lines> @ 3961af94fa62`.

| Proposed key | Citation | Statement | Reason |
|---|---|---|---|
| LEDGER-SEC-01 | :21-28 | Clients sanitize HTML, active content, bidi/zero-width/tag characters, terminal control sequences; keep Agent slash commands distinguishable | client-side rendering rules (unobservable) |
| LEDGER-SEC-02 | :23-24,50 | Clients do not open links, run commands, change settings, or send data from Agent text alone; show the full target and confirm for non-http(s) | client-side, unobservable |
| LEDGER-SEC-03 | :34-37 | Client remote-URI fetch rules: `data` preferred, https/data only, no credentials, refuse loopback and private networks, bound size, no SVG scripts, no out-of-root `file:` reads | client-side, unobservable |
| LEDGER-SEC-04 | :13 | `clientInfo`/`agentInfo` not used for security decisions; Client identifies the Agent from launch configuration | internal decision logic. The TCK itself only records `agentInfo` (`plugin.py:757-760`). |
| LEDGER-SEC-05 | :55-56 | Use only trusted intermediaries; intermediaries do not answer permission requests or elicitations except under user policy | the TCK is a direct client with no intermediary, so there is nothing to assert on |
| LEDGER-SEC-06 | :28 | Client MAY bound or throttle permission requests, elicitations, output | optional and client-side |
| LEDGER-SEC-07 | :51 | Clients send only trusted content as `systemPrompt`; Agents MAY reject it | the client half is client-side; the agent half is MAY (not requirable). The stated MUST rejection rules stay under ACP-SYSPROMPT-002/003. |
| LEDGER-SEC-08 | :38 | Agents apply root-set and fetch rules to URIs in prompts | SHOULD, but needs a network canary, and agents are not required to dereference links. A quiet agent proves nothing and the TCK should not host listeners. Unsafe/out of scope. |
| LEDGER-SEC-09 | :47 | Agents treat embedded resources, files, tool results, and MCP results as data, not user instructions | model behavior, non-deterministic. Prompt-injection detection is stated out of scope at :15. |
| LEDGER-SEC-10 | :48-49 | Agents request permission before off-machine sends after untrusted reads, and before writing execution/approval-controlling files | needs a real tool-using turn with agent-specific triggers; permission requests are advisory (:12), and the agent decides |
| LEDGER-SEC-11 | :57 | A multi-user Agent scopes `session/list`, load/resume, permission requests, and elicitations to the owning user | no user identity on the wire; deployment property |

Also noted, not ledgered because it is a non-testable documentation duty: line 42 ("no credentials in `_meta`"; the checkable part is the cross-doc candidate) and line 61 (custom transports document security considerations).

## Testability notes

- Every Client-bound rule is unobservable from a client-side TCK. The TCK's role is the client. Agents cannot see how the client renders content.
- Agent-bound rules (lines 38, 47-49, 57) depend on model behavior or deployment. The only deterministic check is the secret-echo candidate, which comes from `session-setup.mdx`.
- No conforming/non-conforming fixture distinction exists for this doc, apart from the candidate above.

## Discrepancies

None found.
- Draft and stable `security.mdx` differ only in link prefixes (verified with `git diff` between the two files at the target revision).
- No schema field description conflicts with these statements (I did not do an exhaustive scan of `$defs` descriptions, since nothing in this doc names a schema type beyond `_meta`, `uri`, `data`, and `systemPrompt`).
- Reference SDKs were not consulted.

## Open questions

1. **TCK as a terminal-printing client (line 26).** The TCK prints agent stderr and transcripts into pytest output and the JSON report. `src/tck/common/report.py:72-87` carries raw `transcript` and `stderr`. I did not find any control-sequence neutralization in `src/tck/common`. This is a self-hygiene question for the orchestrator or a maintenance item, not a conformance requirement. A hostile agent could inject terminal escape sequences into the operator's terminal. I did not verify how `plugin.py` prints failure details.
2. The secret-echo candidate (above) needs an owner. It is probably the session-setup report.
3. `session-setup.mdx:473` ("Agents SHOULD NOT treat model output ... as granting access outside the root set") and `tool-calls.mdx:383` (locations are display-only) are agent-internal SHOULDs in other docs. They are likely ledger items for the respective reports, not this one.
