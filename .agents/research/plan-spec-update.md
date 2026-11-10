# Plan: ACP TCK spec update, beac4ba9 -> 3961af94 (v1 and v2)

**Sources checked:** the 25 impact reports and 2 inventories in `.agents/research/` (v1 `impact-v1-*.md` x12, v2 `impact-v2-*.md` x13, `spec-diff-v{1,2}.md`); `src/tck/v{1,2}/requirements.py` (ids, tiers, the v2 id convention at `src/tck/v2/requirements.py:7-13`); `src/tck/v{1,2}/conformance/_helpers.py` (permission selection); `tests/v2/test_registry.py:345-390` (pointer scan covers `.py` files too); `spec-tracker/maps/v{1,2}.toml`; `cross-check/run.sh:118-165`; `.claude/skills/update-to-spec/SKILL.md` step 6. Spec checkout `agent-client-protocol-2` @ `3961af94fa62`, read with `git show`. I used it for one conflict check only (C-R1 below).
**Confidence:** high for the dedup and the slice mechanics, which come straight from the reports and the registries. Medium for the cross-check predictions: they are hypotheses taken from the reports' SDK reading, and nothing has been run.

Report shorthand used below: `v1-err` = `impact-v1-error.md`, `v1-ss` = session-setup, `v1-ld` = session-list-delete, `v1-auth` = auth-cancel-elicitation, `v1-cmc` = config-modes-commands, `v1-apc` = agent-plan-content, `v1-oet` = overview-ext-transports, `v1-pt` = prompt-turn, `v1-sch` = schema, `v1-sec` = security, `v1-tfs` = tools-terminals-fs, `v1-init` = initialization. `v2-*` follows the same pattern: `oe` overview-error, `tr` transports, `ext`, `init`, `ss`, `ldf` list-delete-fork, `cc` config-commands, `ae` auth-elicitation, `can` cancellation, `pl` prompt-lifecycle, `cs` content-security, `tcp` tool-calls-plan, `sch`.

## Executive summary

| | v1 | v2 |
|---|---|---|
| Retire | 1 (INFO-UNKNOWNSESSION-001) | 14, plus 2 renames if V2-D1/D2 are accepted (TRANSPORT-201, SHUTDOWN-001) |
| Retier in place | 0 | 2 (AUTH-201 ADVISORY->MANDATORY, EXT-203 INFORMATIONAL->ADVISORY) |
| New (recommended) | 20, plus 7 optional | 67, plus 2 replacement ids from renames and 17 optional |
| Changed text/test | 7, plus 4 optional | ~33 |
| Hand citation fixes in slice 0 | ~20 rows | ~35 rows/sources |
| Mechanical `--fix` remaps | ~45 of 67 line-cited rows | ~75 of 113 line-cited rows |
| Ledger proposals in reports, then after policy C6 | ~55, ~35 | ~110, ~65 |

There are **59 decisions** (10 cross-cutting, 18 v1, 31 v2). Each one comes with a recommendation. Two findings need nobody's input: re-vendoring v1 breaks nothing (195/195 green with the target schema, `v1-sch`), and re-vendoring v2 breaks only the pointer test and the enum-set test (`v2-sch` Task 5: 103/103 `test_cli` pass).

**Conflict between reports, resolved (C-R1).** `v2-ae` Discrepancies says `schema/v1/schema.unstable.json` at target has no `AuthStatus` `$def`. That is false. `git show 3961af94:schema/v1/schema.unstable.json` has `AuthStatusResponse` (line 3456) and `AuthStatusRequest` (line 6971), and `meta.unstable.json` lists `auth/status` and `auth/status_update`. `v1-sch` and `v1-auth` are correct.

---

## 1. Requirement change table: v1

The table covers rows that change or are proposed. It omits pure `--fix` remaps (~45 rows).

| Id | Class | Tier (current -> proposed) | Rule (one line) | Source |
|---|---|---|---|---|
| ACP-JSONRPC-001 | hand cite (Rust path) | M | `agent-client-protocol-schema/src/rpc.rs:14-16` -> `src/v1/rpc.rs:11-13` (`--fix` only handles `.mdx`) | v1-err |
| ACP-SESSION-003 | hand cite (Needs review) | M | `468,476-501` -> `480,488-513` | v1-ss |
| ACP-LOAD-001 | hand cite + prose | CAP | `106,110-201`; the prose "`{}` example at 191-200" -> `192-201` | v1-ss |
| ACP-LOAD-002, ACP-CLIENTCAP-005 | hand cite | CAP / M | session-setup `136-142`/`139-142` stay as written (bullets became paragraphs) | v1-ss |
| ACP-ADDDIRS-001 | hand cite | CAP | `351-380` -> `354-383` | v1-ss |
| ACP-AUTH-003 | hand cite | CAP | `authentication.mdx:136-167` stays (bold only) | v1-auth |
| ACP-AUTH-004 | hand cite | CAP | `190-213` -> `196-219` (Launch-safety block inserted) | v1-auth |
| ACP-JSONRPC-006/007 | hand cite | M | `cancellation.mdx:12-14`, `16-22` stay | v1-auth |
| ACP-CONFIG-001/002/003 | hand cite | CAP/CAP/M | `118-130,245`; `304,373-377`; `207-209` + `initialization.mdx:189-198` (a mechanical remap of base 172 lands in the new Plan section) | v1-cmc, v1-init |
| ACP-PROMPT-001/003, PROMPTCAP-001..003 | hand cite | M / CAP | `initialization.mdx:247` -> `:264`; `266-270`, `272-274`, `276-278` | v1-init |
| ACP-CLIENTCAP-007 | verify cite | M | RFD `subagents.mdx:72-74` -> `76-78` (`--fix` should do it; verify) | v1-pt |
| ACP-INFO-UNKNOWNSESSION-001 | **retire** | INFO -> (gone) | Premise "v1 does not specify one" is false. Replaced by ACP-ERROR-003 (`INFO-` prefix = INFORMATIONAL only) | v1-err, v1-ss, v1-cmc |
| ACP-INFO-PARSE-001, ACP-INFO-INVALIDREQ-001 | text + cite | INFO | "Spec silent" -> "error.mdx assigns -32700/-32600 but requires no reply; probe breaks client MUST NOT". Add `error.mdx:28`/`:29` | v1-err |
| ACP-JSONRPC-002/004, ACP-ERROR-001/002 | cite add | M/ADV/ADV/ADV | Add `error.mdx:6-10`, `:41-43`, `:9`, `:31,45-47`. JSONRPC-004 stays ADVISORY (v1 error.mdx says SHOULD) | v1-err |
| ACP-SYSPROMPT-001..003 | text | CAP | Drop "Unstable feature." Keep `schema.unstable.json` pointers (CLAUDE.md convention) | v1-ss, v1-init |
| ACP-PROMPT-003 | text + cite | M | `resource_link` MUST is now explicit (`content.mdx:170`). Drop the stale rationale | v1-apc |
| ACP-CLIENTCAP-007 | text + test | M | Also forbid `{"type":"session"}` tool-call content without `subagents` (V1-D10) | v1-tfs |
| ACP-AUTH-006 | text (if C2=B) | M | "null `args`/`env` counts as omitted" | v1-sch |
| ACP-JSONRPC-007, CONFIG-001/002 | optional text | — | Clarifications only, no assertion change | v1-auth, v1-cmc |
| ACP-ERROR-003 | **new** | ADV | `session/prompt` on an unknown or closed session -> `-32002` + `data.sessionId` (close probe test-gated) | v1-err (**merge M1**) |
| ACP-ERROR-004 | **new** | ADV | Same rule for `set_mode`/`set_config_option`/`load`/`resume` (per-test gates) | v1-err, v1-cmc |
| ACP-ERROR-005 | **new** | ADV | A request before `initialize` -> `-32600` | v1-err |
| ACP-ERROR-006 | **new** | ADV | An unadvertised stable gated method -> `-32601` (inverted gate) | v1-err |
| ACP-ERROR-007 | **new** | ADV | Unknown `modeId`/`configId`/value -> `-32602` | v1-err, v1-cmc |
| ACP-ERROR-008 | new, optional | ADV | Reserved-range codes are ACP-defined | v1-err |
| ACP-CLOSE-003 | **new** | ADV | A second close, or a close of a never-created id -> `{}` (`-32002` is an ADVISORY FAIL) | v1-ss, v1-err X1 (**merge M15**) |
| ACP-SESSION-006 | **new** | ADV | An MCP `env` canary never appears on stdout/stderr | v1-ss, v1-sec (**merge M3**) |
| ACP-SESSION-005 | new, optional | ADV | Stdio MCP `args` reach the server verbatim | v1-ss |
| ACP-LIST-003 | **new** | ADV | Never-issued cursor -> `-32602` | v1-ld, v1-err X2 (**merge M16**) |
| ACP-PLAN-001 | **new** | M (vacuous) | `plan_update` file `uri` is absolute (connection advertises `plan: {}`) | v1-apc, v1-init (**M10**) |
| ACP-PLAN-002 | **new** | ADV | Client advertised `plan` -> no baseline `plan` update | v1-apc |
| ACP-PERM-001/002 | **new** | ADV | Honour `reject_once`; an unknown `optionId` is not approval (file side effect) | v1-tfs |
| ACP-AUTH-007 | **new** (C1) | CAP `agentCapabilities.auth.status` | `auth/status` before auth -> valid `AuthStatusResponse`, never `-32000` | v1-auth |
| ACP-AUTH-008 | **new** (C1) | ADV | `state` is defined or `_`-prefixed | v1-auth |
| ACP-ARCHIVE-001..006 | **new** (C1) | CAP `...sessionCapabilities.archive` | archive needs list; boolean `archived`; round-trip/filter views; bad filter `-32602`; idempotent, unknown id is an error; deleted session absent under every filter | v1-ld (001 also from v1-init's "LIST-003" candidate, **M17**) |
| ACP-ARCHIVE-007 | new, deferred | CAP | Archiving cancels an in-flight prompt | v1-ld |
| ACP-TITLE-001/002, ACP-SESSIONSTATUS-001/002 | new, **deferred** (C1) | CAP / ADV | set_title / status smoke rows | v1-ld |

Next free v1 numbers after this plan: ERROR-009, CLOSE-004, SESSION-007, LIST-004, PLAN-003, PERM-003, AUTH-009, ARCHIVE-008. Retired numbers are never reused.

## 2. Requirement change table: v2

Convention check, from `src/tck/v2/requirements.py:7-13`: a bare v1 id is reused in v2 only when text **and** tier match v1, and a changed tier means a fresh `2xx` id. That forces retire-plus-new for the bare ids JSONRPC-004 and SHUTDOWN-001, and it is the reason behind the TRANSPORT-201 -> 001 rename. 2xx ids may be retiered in place. New v2-only rows always get 2xx numbers, so the content report's `PROMPTCAP-004` becomes `ACP-PROMPTCAP-201`.

### 2a. Slice-0 hand citation fixes (registry and `.py`; `test_registry` scans both)

| Id / file | Fix | Source |
|---|---|---|
| ACP-AUTH-202 | `#/$defs/AuthCapabilities` -> `#/$defs/ClientAuthCapabilities` | v2-sch, v2-ae |
| ACP-EXT-203 + `test_extensibility.py:218` docstring | `#/$defs/ProtocolLevelNotification` (removed) -> `extensibility.mdx:165,231`, `error.mdx:44` (+ optional positional `#/anyOf/2/properties/params/anyOf/0`) | v2-sch, v2-ext |
| ACP-JSONRPC-001/002 | `#/anyOf/3/items` -> `#/$defs/AgentResponse`. JSONRPC-001 also drops `transports.mdx:76-81` (past EOF) for `overview.mdx:15-17,233` | v2-sch, v2-tr, v2-oe |
| ACP-BATCH-201/207 | Dangling `#/anyOf/{2..5}/minItems`, `#/anyOf/4/items` -> temporary `transports.mdx:65-67`. Rows are retired in S-v2-1 | v2-sch |
| **ACP-TRANSPORT-201, ACP-INFO-BATCH-202** | **Silent hazard:** `#/anyOf/2`/`#/anyOf/3` now resolve to ProtocolLevel/Proxy. Repoint to `#/anyOf` + `transports.mdx:20,23,67` (TRANSPORT) and `:65-67` (INFO-BATCH) | v2-sch, v2-tr |
| ACP-JSONRPC-003 | Drop deleted `transports.mdx:76-79`; cite `overview.mdx:10,227` | v2-oe, v2-tr |
| ACP-CANCEL-205 | Drop deleted `transports.mdx:78-79`; cite `overview.mdx:13,151-153,227` | v2-can, v2-tr |
| ACP-CLIENTCAP-202 | `meta.unstable.json:31-37` (wrong at base) -> `:28-35,36-38` | v2-sch, v2-ext |
| ACP-CLIENTCAP-201 | `elicitation.mdx:187` (deleted) -> `:56-57,59` | v2-ae |
| ACP-INIT-003/202/206 | Meaning moved: `:98,117` -> `:108,110,112`; INIT-206 -> `:108` (mechanical would land on :129) | v2-init |
| ACP-RESUME-202 | Deleted notices text `:212-215` -> `:225-229` (+`:138`) | v2-ss |
| ACP-RESUME-209 | Deleted `:192-195` -> `:207-209,221,282-284` | v2-ss |
| ACP-CONFIG-206 | Range meaning moved -> `session-config-options.mdx:236,373,459` | v2-cc |
| ACP-INFO-CONCURRENT-201 | Cited sentence deleted -> `prompt-lifecycle.mdx:382-384` (text fixed in S-v2-7) | v2-pl |
| ACP-STATE-203 | Pre-existing: `IdleStateUpdate/anyOf/7` (`none`) -> `anyOf/6` (`other`) | v2-ext |
| ACP-PROMPT-205 | `schema.mdx:8397-8401` -> `#/$defs/SubagentUpdate` (name-stable) | v2-sch |
| ACP-FORK-201/202 | Drop `schema.mdx:614-624/622-624`; cite `initialization.mdx:269-273`, `session-setup.mdx:49`, `error.mdx:54`, `#/$defs/ForkSessionResponse/properties/sessionId` (**merge M21**: no positional `ClientRequest` pointers) | v2-ldf, v2-sch |
| ACP-CANCEL-201/202/204, ACP-AUTH-205 | Keep `schema.mdx` line cites; verify `--fix` lands on 603-607 / 615-617 / 595-597 / 954 | v2-sch, v2-can |
| ACP-ENUM-201 | `tool-calls.mdx:419` hunk: Needs review | v2-tcp |

### 2b. Semantic changes

| Id | Class | Tier (current -> proposed) | Rule | Source |
|---|---|---|---|---|
| ACP-BATCH-201..208, ACP-INFO-BATCH-201/202 | **retire** (10) | various -> gone | Batching removed. 202/203/207 are inverted | v2-tr |
| ACP-BATCH-209 | **new** | ADV (V2-D3) | Any array on stdin -> one `-32600`/`id:null`, no element processed | v2-tr |
| ACP-TRANSPORT-201 -> ACP-TRANSPORT-001 | text + **rename** (V2-D1) | M | Every stdout line is a single object; an array is non-conformant. Also marked on the BATCH-209 test | v2-tr (**M19**) |
| ACP-TRANSPORT-203 | text | M | Drop the batch clause; cite `:21` | v2-tr |
| ACP-SHUTDOWN-001 -> ACP-SHUTDOWN-201 | text + **rename** (V2-D2) | ADV | SHOULD exit after stdin EOF (`transports.mdx:43`) | v2-tr |
| ACP-JSONRPC-001/003/005 | text | M/M/ADV | Drop the batch halves; 005 evidence = BATCH-209 follow-up | v2-tr, v2-oe |
| ACP-JSONRPC-002 | text + validation | M | Result `id` int/string; only error may be `null` | v2-oe, v2-sch |
| ACP-JSONRPC-004 | **retire** | ADV -> gone | Now MUST (`extensibility.mdx:202`, `error.mdx:44`) | v2-oe, v2-ext (**merge M5**) |
| ACP-JSONRPC-201 | **new** | M | Unknown `_` method -> `-32601` (replaces 004) | v2-oe, v2-ext |
| ACP-JSONRPC-202 | **new** | M | Agent request `id` int/string, not reused while pending | v2-oe |
| ACP-ERROR-001 | text | ADV | Drop "byte-identical to v1"; add `error.mdx:6-10` | v2-oe |
| ACP-INFO-UNKNOWNSESSION-001 | **retire** | INFO -> gone | Now MUST `-32002` + `data.sessionId` | v2-oe, v2-ss |
| ACP-ERROR-201 | **new** | CAP `capabilities.session` | `session/prompt` on a never-created or closed session -> `-32002` + `data.sessionId` (sub-probe: `set_config_option` when configOptions present) | v2-oe, v2-ss SESSION-205, v2-cc (**merge M1**) |
| ACP-ERROR-202 | **new** | M | Unadvertised gated standard method -> `-32601` | v2-oe |
| ACP-ERROR-203 | **new** | ADV | Reserved-range codes are ACP-defined | v2-oe |
| ACP-ERROR-204 | new, optional | ADV | If a non-JSON line is answered: `-32700`, `id:null` | v2-oe |
| ACP-INFO-PARSE-001/INVALIDREQ-001 | text | INFO | Same edit as v1 | v2-oe |
| ACP-EXT-001 | text | M | `-32601` is now JSONRPC-201's concern | v2-ext |
| ACP-EXT-203 | **retier** + text | INFO -> ADV | `$/` unknown notification ignored (SHOULD) | v2-ext |
| ACP-META-001 | cite + test hygiene | ADV | Probe key `"tck"` is ACP-reserved (C3) | v2-ext, v2-sch |
| ACP-META-202 / 203 | **new** | ADV / CAP | Non-object `_meta` treated as omitted / W3C trace keys formatted | v2-ext |
| ACP-META-204 | new, optional | ADV | Agent `_meta` keys namespaced | v2-ext |
| ACP-ENUM-201 | text (sites) | CAP | + `paused`, `session` (slice 0); + plan/diff sites; fix chunk loop bug | v2-ext, v2-tcp |
| ACP-ENUM-204 | new, optional | ADV | Embedded resource with neither text nor blob is rejected (was ext "ENUM-205", renumbered) | v2-ext (**M13**) |
| ACP-INIT-209..214 | **new** (6) | M (211-213: V2-D7) | Pre-init `-32600`; agent silent pre-init; retry after failure; repeat before other request; repeat after request `-32600`; unparseable newer params tolerated | v2-init (**M6**: cite `error.mdx:29,60`; no ERROR id) |
| ACP-SESSION-204 | **new** | CAP | Relative `cwd` -> `-32602` | v2-ss |
| ACP-SESSION-206/207 | **new** | ADV | No session-scoped request / config/commands update before the `session/new` response | v2-ss |
| ACP-SESSION-208 | **new** | CAP | A list notified early must also be in the response | v2-ss |
| ACP-CONFIG-203 | text (shape only, non-empty) | CAP | Presence moves to RESUME-210 | v2-ss, v2-cc (**merge M7**) |
| ACP-RESUME-210 | **new** | CAP | Resume carries `configOptions`/`availableCommands` when the session's own `session/new` did | v2-ss, v2-cc D1 |
| ACP-RESUME-211 | **new** | CAP | Resume of a never-created id -> `-32002` (shared `-32002`+`data` helper) | v2-ss (**M1**) |
| ACP-RESUME-212/213 | **new** | CAP | No replayed historical active `state_update`; background items announced before the snapshot | v2-ss |
| ACP-RESUME-214, 216 | **new** | ADV | `session_info_update` before resume; resume of a session active on this connection succeeds | v2-ss |
| ACP-RESUME-215 | new, optional | ADV | Replayed tool calls end final | v2-ss |
| ACP-RESUME-201 | cosmetic text | CAP | Drop the stale "B3" label | v2-ss |
| ACP-CLOSE-204 | text | ADV | `-32002` becomes a third legal outcome | v2-ss |
| ACP-CLOSE-205 | **new** | CAP | `session/close` sends `$/cancel_request` for a pending permission before responding | v2-ss + v2-can N6 (**merge M2**, one id) |
| ACP-CLOSE-206 | **new** | CAP | No session messages after the close response | v2-ss |
| ACP-CLOSE-207 | **new** | ADV | Closing an already-closed session -> `{}` | v2-ss |
| ACP-ADDDIRS-203 | **new** | CAP `...additionalDirectories` | Relative entry -> `-32602` | v2-ss |
| ACP-MCP-201 | text (rationale) | INFO | Cite `:685` | v2-ss |
| ACP-MCP-203 | **new** | CAP | Unsupported transport -> `-32602` (probes `sse` and `_tck_unsupported_transport`) | v2-ss + v2-ext "ENUM-206" (**merge M11**) |
| ACP-MCP-204 | **new** (V2-D10) | ADV | Duplicate server names -> `-32602` | v2-ss |
| ACP-MCP-205 | **new** | ADV | MCP `env`/header canary never echoed | v2-ss, v2-cs (**M3**) |
| ACP-LIST-203 | text + test | CAP | `_same_dir` compare; a subdirectory session is excluded | v2-ldf |
| ACP-LIST-205 / 206 | **new** | CAP | Relative `cwd` filter / never-issued cursor -> `-32602` | v2-ldf |
| ACP-DELETE-201 | text + test | CAP | Delete an active idle session (V2-D12) | v2-ldf |
| ACP-DELETE-202 | test | CAP | `-32002` delete reply counts as success, then judge the listing | v2-ldf |
| ACP-DELETE-203 | message + cite | ADV | Keep FAIL on `-32002`; cite `error.mdx:56` | v2-ldf |
| ACP-DELETE-204 / 205 | **new** | CAP `...delete` | Delete cancels in-flight work / resume after delete -> `-32002` | v2-ldf |
| ACP-FORK-202 | rider text | CAP | Now defined in the draft docs | v2-ldf |
| ACP-FORK-203 | **new** | CAP `...fork` | Fork of an unknown session -> `-32002` | v2-ldf (**M1**) |
| ACP-FORK-204 | new, optional | CAP | Fork of a closed, listed session succeeds | v2-ldf |
| ACP-ARCHIVE-201..207 | **new** (C1) | CAP `...archive` | Round-trip; `archived` flag; views; unknown -> `-32002`; bad filter -> `-32602`; cancels work; idempotent | v2-ldf |
| ACP-SESSIONSTATUS-201..203, ACP-TITLE-201..203 | new, **deferred** (C1) | CAP | Smoke rows (report used `STATUS-*`; renamed per C8) | v2-ldf |
| ACP-CONFIG-201/202/204 | text | CAP | Non-empty options; MUST support set; membership is an explicit MUST | v2-cc |
| ACP-CONFIG-207..210 | **new** | CAP `inferred:configOptions` | Unknown `configId` / invalid value (including unsupported value `type`) -> `-32602`; rejection leaves state unchanged; select values unique | v2-cc (+ v2-ext "ENUM-207" folded into 208, **M12**) |
| ACP-CONFIG-211/212 | **new** | ADV | Set sends `config_option_update`, before the response | v2-cc |
| ACP-COMMANDS-201 | **new** | CAP `inferred:availableCommands` | Commands typed; names have no whitespace and are unique | v2-cc |
| ACP-AUTH-201 | **retier** | ADV -> M | `methodId` unique (`authentication.mdx:51`) | v2-ae |
| ACP-AUTH-202 | text | M | Prose is now MUST NOT (`:149-151`) | v2-ae |
| ACP-AUTH-204 | optional tightening | CAP | `-32602` for an advertised `agent` id FAILs | v2-ae |
| ACP-AUTH-208 | **new** | CAP `inferred:authMethods` | Unadvertised `methodId` -> `-32602` | v2-ae |
| ACP-AUTH-209 | **new** (C1) | CAP `capabilities.auth.status` | `auth/status` valid, never `-32000`/`-32601`, `state` open-enum | v2-ae |
| ACP-CANCEL-204 | text | INFO | "...of the cancelled foreground work" | v2-can |
| ACP-CANCEL-209 | text + test | CAP | Strict hold: the TCK leaves the permission request unanswered (V2-D16) | v2-can |
| ACP-INFO-CANCEL-201 | text | INFO | Also record the non-active-session case | v2-can |
| ACP-INFO-CANCEL-202 | **retire** | INFO -> gone | Now SHOULD | v2-can (**M20**) |
| ACP-CANCEL-210 / 211 | **new** | M | `$/cancel_request` for an unknown / already-answered id gets no response | v2-can |
| ACP-CANCEL-212 | **new** | CAP | A withdrawn prompt is still answered exactly once | v2-can |
| ACP-CANCEL-213 | **new** | ADV | Cancel withdraws the pending permission via `$/cancel_request` (replaces INFO-CANCEL-202) | v2-can |
| ACP-CANCEL-214 | **new** | CAP | A held prompt covered by cancel -> `-32800`, never inserted later | v2-can N5 (**merge M8** with PROMPT-209 scenario) |
| ACP-PROMPT-206 | text + cite | CAP | `content.mdx:178` now states the MUST | v2-cs |
| ACP-PROMPT-208 | **retire** (V2-D17) | ADV -> gone (+ledger) | Response-vs-idle order is now meaningless (PL:372) | v2-pl |
| ACP-INFO-CONCURRENT-201 | text | INFO | Record inserted-vs-held | v2-pl |
| ACP-PROMPT-209 | **new** | CAP (V2-D17) | A prompt during active work is not rejected | v2-pl |
| ACP-PROMPT-210 | new, optional | ADV | Held prompts are inserted in received order | v2-pl |
| ACP-PROMPT-211 | **new** | CAP | `_`-typed unknown content block -> `-32602`, no insertion | v2-pl PROMPT-211, v2-cs PROMPT-209, v2-ext ENUM-204 (**merge M4**) |
| ACP-PROMPTCAP-201 | **new** | CAP (runtime negative gate) | Unadvertised `image`/`audio`/`resource` -> `-32602` | v2-cs "PROMPTCAP-004", v2-pl PROMPT-211 (**M4**) |
| ACP-STATE-206..208 | **new** | CAP | `background` persists once reported; items announced; items finalized before removal (judged at idle only) | v2-pl |
| ACP-PERM-202 / 203 | **new** | CAP | Unique `optionId` + absolute command `cwd` / no `completed` after a `cancelled` outcome | v2-tcp |
| ACP-PATCH-208 / 209 | test / text | ADV | First report includes chunks and permission subjects / background-work permission excluded | v2-tcp |
| ACP-PATCH-210..212 | **new** | ADV | Status monotonic / unlisted calls final at idle / `cancel` capability dropped when final | v2-tcp (**M9**: 212 stays passive) |
| ACP-DIFF-201, ACP-PLAN-201, ACP-PATCH-213/214 | new, **deferred** | — | Pre-existing or unstable rules, low value now | v2-tcp |

## 3. Merges (dedup log)

| # | Merged proposals | Final |
|---|---|---|
| M1 | Unknown session `-32002`+`data.sessionId`: v2-oe ERROR-201, v2-ss SESSION-205 & RESUME-211, v2-ldf DELETE-205/FORK-203/ARCHIVE-204/STATUS-202/TITLE-202, v2-cc (set_config_option); v1-err ERROR-003/004, v1-cmc Q1, v1-ss Q | v2: ERROR-201 (prompt never-created + closed; set_config_option sub-test) absorbs SESSION-205. RESUME-211, DELETE-205, FORK-203 and the archive instance stay feature-gated ids, **all using one assertion helper (code + `data.sessionId`)**. v1: ERROR-003 + ERROR-004 |
| M2 | Close sends `$/cancel_request` for a pending permission: v2-ss CLOSE-205, v2-can N6 CLOSE-205 | One ACP-CLOSE-205, built in the cancellation slice (shares the hold machinery and the `AsksPermissionAgent` fix). v2-ss CLOSE-206/207 keep their numbers |
| M3 | MCP env/header secret echo: v1-ss SESSION-006 + v1-sec candidate; v2-ss MCP-205 + v2-cs SEC-07 | v1 ACP-SESSION-006, v2 ACP-MCP-205 (ADVISORY, no persist/log coverage claimed) |
| M4 | Unknown/unadvertised prompt content `-32602`: v2-ext ENUM-204, v2-cs PROMPT-209 + PROMPTCAP-004, v2-pl PROMPT-211 | ACP-PROMPT-211 (`_` probe) + ACP-PROMPTCAP-201 (known type, negative gate). PROMPT-209 goes to v2-pl's active-work row |
| M5 | v2 JSONRPC-004: v2-ext retier in place vs v2-oe retire + JSONRPC-201 | Retire + JSONRPC-201. A bare v1 id cannot change tier (`v2/requirements.py:7-13`). The `INFO-`/tier-in-id convention is not the reason: INFORMATIONAL ids without `INFO-` exist (CANCEL-204, BATCH-205..208, MCP-201/202) |
| M6 | v2 INIT-209/213 vs the error.mdx:60 pre-init rule | INIT-209/213 own it, citing `error.mdx:29,60` + `initialization.mdx`; no ERROR id |
| M7 | v2 CONFIG-203 presence (v2-cc D1) vs RESUME-210 (v2-ss) | CONFIG-203 shape-only (+non-empty); RESUME-210 checks presence of both lists |
| M8 | CANCEL-214 vs PROMPT-209 | One scenario helper in one slice. PROMPT-209 judges "no rejection before cancel"; CANCEL-214 judges the post-cancel `-32800` |
| M9 | PATCH-212 vs the tool_call/terminal cancel deferral | PATCH-212 is passive and needs no `tool_call/cancel` probe, so it stays. The ledger entry for the cancel contract excludes it |
| M10 | ACP-PLAN: v1-apc PLAN-001/002, v1-init routing, v2-tcp optional PLAN-201 | v1 PLAN-001/002 now; v2 PLAN-201 deferred. V1-D12 ("absolute") also binds v2 later |
| M11 | v2-ext ENUM-206 vs v2-ss MCP-203 | MCP-203, both probe values |
| M12 | v2-ext ENUM-207 vs v2-cc CONFIG-208(d) | CONFIG-208 |
| M13 | v2-ext ENUM-205 (once 204/206/207 are folded) | Renumbered ENUM-204 (optional) |
| M14 | v1 `SESSIONSTATUS` vs v2 `STATUS` area | `SESSIONSTATUS` in both (C8) |
| M15-M17 | v1 CLOSE-003 (v1-err X1 + v1-ss); v1 LIST-003 (v1-ld + v1-err X2); v1-init "LIST-003 archive requires list" | CLOSE-003; LIST-003 = invalid cursor; archive-requires-list = ARCHIVE-001 |
| M18 | `x-deserialize-default-on-null`: v1-sch D1, v1-auth Q1, v1-ss Q, v2-ae AUTH-207 note | One decision, C2 |
| M19 | TRANSPORT row vs BATCH-209 | Double marker on the BATCH-209 test (an agent array reply = MANDATORY FAIL) |
| M20 | v2 INFO-CANCEL-202 | Retire -> CANCEL-213 |
| M21 | FORK cites: v2-sch "keep schema.mdx lines" vs v2-ldf "repoint to draft docs" | Draft docs + name-stable pointers for FORK. Line cites kept only where the prose lives in positional branches (CANCEL-201/202/204, AUTH-205) |

## 4. Decisions

### Cross-cutting (decide first)

| # | Decision | Options | Recommended, and why |
|---|---|---|---|
| C1 | Scope of new unstable methods | A all CAPABILITY now; B all ledger; **C split** | **C:** add **archive** (v1 ARCHIVE-001..006, v2 201..207) and **auth/status** (v1 AUTH-007/008, v2 AUTH-209) now. **Defer** `session/status` and `session/set_title` (one ledger entry per method family, plus planned optional rows S-v1-11/S-v2-18), `tool_call/cancel` and `terminal/cancel` (ledger; per-entity dynamic gate, not elicitable), and v1 ARCHIVE-007. Put **proxy/\*** in the ledger in both versions. Why: archive has a draft-doc section with MUSTs, and auth/status is a safe pure query whose `-32000` MUST NOT is in the schema. For status and title the RFD contradicts the schema on unknown ids, there is no doc section, and Python has not adopted them |
| C2 | `null` on `x-deserialize-default-on-null` agent-authored fields | A strict; **B hint-aware** | **B:** drop a `type` error when the instance is `null` and the schema node carries the hint. Apply it to v1 (AUTH-006, `terminal/create`) and v2 (AuthMethodTerminal `args`/`env`). It is schema-derived and self-updating, and both reference receivers accept null. Optional ADVISORY "send `[]`/omit" |
| C3 | TCK's own `_meta` key `"tck"` and `_tck/*` probe names | A keep; **B rename `_meta` key only**; C also rename methods | **B,** in both versions in one slice: `"tck"` sits in ACP-reserved space in v2 (`extensibility.mdx:102`). `_tck/*` methods are conforming (the `_` MUST). Rename them only if the user wants cosmetics, and then update CLAUDE.md step 4. **Domain is the user's choice.** It cannot be `com.example`, or any prefix whose second label is `agentclientprotocol` |
| C4 | Mock-client permission choice. v1 picks the **first** option (`v1/_helpers.py:410`); v2 picks the **first `allow_*`** (`v2/_helpers.py:764-774`). Either can select `allow_always` and persist it in the operator's real agent | A keep; **B by kind** | **B,** both versions: `allow_once`, then `allow_always` only if no `allow_once` exists (record a property), then the first option. Add a per-test policy hook (reject_once / unknown id / decline-by-`cancelled` / hold), which v1 PERM-001/002, v2 PERM-203 and strict CANCEL-209 need. This follows the Rust reference client (by kind, never by position) |
| C5 | Auth hazards | (i) embedded-login `AgentTimeout`: FAIL (today) vs **SKIP `AUTH-GATED:` with hint**; (ii) `--allow-logout`: document vs **run logout test last**; (iii) v2 custom-type `--auth-method`: **leave** vs require `type:"agent"` | (i) SKIP: an interactive login may stay pending (`v2 authentication.mdx:179`), and a FAIL on every session test is wrong. Applying it to v1 `authenticate` too is a hypothesis. (ii) Order AUTH-004 (v1) / AUTH-203 (v2) last: credentials outlive connections. (iii) Leave it: the operator vouches for the method |
| C6 | Ledger policy (both ledgers are empty; ~165 entries proposed) | A everything; B nothing; **C agent-side only** | **C:** ledger only rules that bind the **agent** and that the TCK deliberately does not test (unobservable, unsafe, out of scope, deferred-unstable). One entry per rule or tight group, plus one "deferred" entry per deferred method family (C1). Omit client-, intermediary- and receiver-UI rules and pure MAYs. When a probe deliberately breaks a client rule, say so in the test docstring, not the ledger. Estimates: v1 ~55 -> ~35, v2 ~110 -> ~65. Each area slice adds its own entries |
| C7 | Retired-id hygiene | A nothing; **B never reuse; optional retired-id list** | **B:** a short `_RETIRED` tuple checked by `test_registry` prevents number reuse. Optional, small |
| C8 | Area names | — | `SESSIONSTATUS` (both versions; avoids clashing with `auth/status` and v2 `STATE`), `COMMANDS` (v2), new v1 areas `PLAN`, `PERM`, `ARCHIVE`, `TITLE` |
| C9 | Strictness of keyword-less "gets `-32002`/`-32602`" | A assert the code in CAPABILITY; **B CAPABILITY asserts error-vs-success, code separately** | **B,** except where a MUST names the code (v2 `error.mdx:54` `-32002`, v2 list cursor). v1's unknown-session code is SHOULD, so it is ADVISORY (ERROR-003/004). Mirrors ACP-SYSPROMPT-002 |
| C10 | Probes that deliberately break client rules (relative cwd, unadvertised methodId/configId/content, arrays, `$/` probe) | A forbid; **B allow where the spec defines the agent's answer** | **B:** use `_tck`-prefixed values and explain in the docstring. This is already the precedent of RESUME-208 and ACP-INFO-PARSE |

### v1

| # | Decision | Recommended (reason) |
|---|---|---|
| V1-D1 | INFO-UNKNOWNSESSION-001: retire vs retier in place | Retire -> ERROR-003 (the `INFO-` prefix is used only for INFORMATIONAL probes) |
| V1-D2 | ERROR-004 as one id vs split by method | One id (one SHOULD sentence; failure messages name the method) |
| V1-D3 | ERROR-006 separate vs folded into JSONRPC-004 | Separate (new text, inverted gate) |
| V1-D4 | ERROR-008 add vs ledger | Add, low priority, ADVISORY (agents with legacy `-32001` codes only get an advisory FAIL) |
| V1-D5 | error.mdx core sections | Whole doc if C1 adds archive (ARCHIVE-005 cites `error.mdx:67`); else `["(intro)","Error codes","Common cases"]` |
| V1-D6 | CLOSE-003: `-32002` FAIL vs PASS | ADVISORY FAIL (client tolerance does not excuse the agent SHOULD) |
| V1-D7 | SESSION-005/006 adopt vs ledger | Adopt 006 (matches v2 MCP-205); ledger 005 (shell-vs-quoting indistinguishable) |
| V1-D8 | LIST-003: wrong code FAIL vs record | FAIL (the SHOULD names `-32602`) |
| V1-D9 | DELETE-003 on a `-32002` delete | Proceed to the list check (`session-delete.mdx:87`); DELETE-002 unchanged |
| V1-D10 | CLIENTCAP-007 extend vs new 008 | Extend (same capability, same RFD gate) |
| V1-D11 | PERM-001/002 add vs ledger | Add, ADVISORY (deterministic fixture, file side effect). Needs C4's hook |
| V1-D12 | PLAN-001 meaning of "absolute" | RFC 3986 scheme present + RFC 8089 path-absolute for `file:` (hypothesis-level reading); PLAN-002 ADVISORY |
| V1-D13 | `ToolCallLocation.line` 1-based | Ledger (the schema keeps `minimum: 0` deliberately upstream) |
| V1-D14 | Extension naming (`extensibility.mdx:117`) / Conventions paragraph | Ledger / no action (Conventions is already enforced by SCHEMA-001) |
| V1-D15 | INIT-004 tier | Keep ADVISORY |
| V1-D16 | JSONRPC-007 tighten to `cancelled` | No; optional text tweak only |
| V1-D17 | Delegated-task SHOULD, `SubagentUpdate.cwd` absolute | Ledger (needs `subagents`, never advertised) |
| V1-D18 | AUTH-008 keep vs drop | Keep ADVISORY (piggy-backs on AUTH-007) |

### v2

| # | Decision | Recommended (reason) |
|---|---|---|
| V2-D1 | TRANSPORT-201 -> 001 rename vs keep 201 | Rename (registry convention). Churn: ~10 `test_cli.py` sites |
| V2-D2 | SHUTDOWN-001 -> 201 vs keep | 201 (the tier already differs from v1; now a real SHOULD) |
| V2-D3 | BATCH-209 ADVISORY vs MANDATORY | ADVISORY (the receiver clause has no keyword) plus the TRANSPORT double marker. Consequence: `crashes_on_batch` stays CONFORMANT |
| V2-D4 | INFO-PARSE/INVALIDREQ tier; ERROR-204 | Keep INFORMATIONAL; add ERROR-204 (both SDKs agree on `-32700`/null) |
| V2-D5 | EXT-203 tier | ADVISORY (new SHOULD at `:231`) |
| V2-D6 | AUTH-201 tier | MANDATORY (`:51` MUST) |
| V2-D7 | INIT-211/212/213 tier; INIT-207 widen vs new rows | MANDATORY (Rust implements them; Python lags); keep INIT-207 narrow |
| V2-D8 | JSONRPC-202 reuse half: register vs ledger | Register both halves, with an explicit SKIP reason |
| V2-D9 | SESSION-204/208, CLOSE-206 tier; RESUME-216 add; CLOSE-204 `-32002` | CAPABILITY / CAPABILITY / CAPABILITY; add 216; accept `-32002` |
| V2-D10 | MCP-203 probe value; MCP-204 add vs ledger | Both probes (`sse`, `_tck_*`); MCP-204 ADVISORY |
| V2-D11 | LIST-206 tier | CAPABILITY (a never-issued token is invalid under any reading of `:72`) |
| V2-D12 | DELETE-201 redesign; DELETE-203 on `-32002` | Delete an active idle session; keep the ADVISORY FAIL |
| V2-D13 | Config: CONFIG-203 (see M7); attribution of B5 failures; tiers | Validate only `configOptions` items in config tests (D2); 207-210 CAPABILITY, 211/212 ADVISORY |
| V2-D14 | COMMANDS-201 encoding | `inferred:availableCommands`, CAPABILITY |
| V2-D15 | AUTH-204 tightening; AUTH-208 probe | Yes (low priority); AUTH-208 CAPABILITY, `_tck_unadvertised_method` |
| V2-D16 | CANCEL-209 strict hold; INFO-CANCEL-201; CANCEL-205 cite | Strict (otherwise the agent MUST is unobservable); keep INFORMATIONAL and record non-active; repoint |
| V2-D17 | PROMPT-208 retire vs INFORMATIONAL; INFO-CONCURRENT-201; PROMPT-209 tier; PROMPT-210; STATE-208 scope | Retire + ledger; keep with new text; CAPABILITY; optional ADVISORY; judge idle-snapshot removals only |
| V2-D18 | PROMPTCAP-201 tier | CAPABILITY (fall back to ADVISORY if cross-check shows widespread non-enforcement) |
| V2-D19 | PERM-203 tier; PATCH-210 tier; PATCH-208 chunk-first; ENUM-201 sites; optional DIFF/PLAN/PATCH-213/214 | CAPABILITY; ADVISORY; FAIL; add every explicit-MUST site except `subject.type`; defer |
| V2-D20 | META-202 / META-203 / META-204 | ADVISORY / CAPABILITY / add later (after C3) as ADVISORY, low priority |
| V2-D21 | ENUM-204 (embedded resource) | Optional, low priority |
| V2-D22 | Spec map: content.mdx core; cancellation.mdx core; error.mdx whole doc; `core_defs` + `RequestId`, `Error` | Yes / yes / yes / yes (all are envelope or cross-cutting rules restated elsewhere) |
| V2-D23 | Positional root-pointer guard in `test_registry` | Yes (would have caught TRANSPORT-201/INFO-BATCH-202) |
| V2-D24 | `run_prompt` H1 (idle before response = candidate) | Yes, in S-v2-7 (PL:372); no current test misjudges without it |
| V2-D25 | `_helpers` array flattening after B1 | Keep tolerant flattening, so a batching agent fails only the TRANSPORT row; `is_agent_initiated` returns False for lists |
| V2-D26 | MCP-201 notice recording | Optional `record_property` |
| V2-D27 | RESUME-213/215 with vacuous-pass fixtures | Register 213 (MUST); 215 optional |
| V2-D28 | Elicitation coverage (`--elicitation-prompt`) | Defer; elicitation MUSTs go to the ledger |
| V2-D29 | ENUM-205->204 numbering, PROMPTCAP-201 numbering | Accept the renumbering (2xx rule, no gaps reused) |
| V2-D30 | `answers_notifications.py`-style `{"id":null,"result":null}` fixtures | Switch to error-shaped bogus replies, so JSONRPC-002 tightening adds no FAIL |
| V2-D31 | Python cross-check pin rc2 -> 1.0.0 | Route to the cross-check owner (it changes the array behaviour from crash to silent-ignore) |

## 5. Spec-map changes

| Map | Change | Slice |
|---|---|---|
| v1 | session-setup `sections = ["(intro)", "Session ID", "Working directory"]` (now also covers Workspace root security, by design) | S-v1-0 |
| v1 | prompt-turn `sections = ["Session updates", "Stop reasons", "Cancellation"]` | S-v1-0 |
| v1 | New `[[core_doc]] docs/protocol/v1/draft/error.mdx` (V1-D5), code: `protocol.py`, `test_jsonrpc.py`, `test_diagnostics.py`, `test_informational.py`, `test_session_capabilities.py`, `_helpers.py` (+ ERROR-00x host module) | S-v1-1 |
| v1 | transports `reason`: drop "no other doc links here" (`security.mdx:61` links it). Optional code adds: transports += `test_informational.py`, overview += `test_prompt.py`, extensibility += `test_jsonrpc.py` | S-v1-9 |
| v1 | `core_defs`: no change (`SessionCapabilities` is already reached through the `AgentCapabilities` closure) | — |
| v2 | prompt-lifecycle `sections` re-cased: `"(intro)"`, `"Session updates > (intro)"`, `"Session updates > Entity IDs"`, `"Foreground and background work"`, `"Prompt lifecycle > (intro)"`, `"1. User message"`, `"2. Prompt accepted"`, `"3. Agent reports output > (intro)"`, **`"3. Agent reports output > Message IDs"` (new)**, `"4. Report completion > (intro)"`, `"5. Tool invocation and status reporting"`, `"6. Continue conversation"`, `"Stop reasons"`, `"Failures"`, `"Session states"`, `"Cancellation"`; re-case the excluded-list comment | S-v2-0 (Message IDs addition may wait for S-v2-7) |
| v2 | session-setup `sections`: **`"Session lifecycle"` (new)**, `"Creating a session"`, `"Initial session state"`, `"Resuming sessions"`, `"Closing active sessions"`, `"Session ID"`, `"Working directory"` | S-v2-0 |
| v2 | overview `sections`: **`"Communication Model"` (new; kept Title Case at target)**, `"Agent > Baseline methods"`, `"Argument requirements"`, `"Error handling"`, `"Conventions"`; code += `test_diagnostics.py` | S-v2-0 |
| v2 | New whole-doc cores: `error.mdx` (code: `test_jsonrpc.py`, `test_diagnostics.py`, the ERROR-201 module, `validation.py`, `protocol.py`), `cancellation.mdx` (code: `_helpers.py`, `test_cancel.py`), `content.mdx` (code: `test_prompt.py`, `test_prompt_capabilities.py`) (V2-D22) | S-v2-3, S-v2-6, S-v2-8 |
| v2 | transports `reason` -> "stdio framing, shutdown, message timing and order, and the no-batches rule that every message exchange depends on"; code += `test_diagnostics.py`; drop `test_batch.py` if renamed | S-v2-1 |
| v2 | `core_defs` += `RequestId`, `Error` | S-v2-2 |
| v2 | Not core (confirmed by the reports): security, session-list/delete, config, slash-commands, tool-calls, agent-plan, authentication, elicitation | — |

## 6. Harness, fixture and stale-comment fixes not tied to one requirement

| Where | Fix | Slice |
|---|---|---|
| v1 `_helpers.py:302`, `tests/fixtures/agents/v1/asks_permission.py:3`, `test_session_capabilities.py:226` | Comment line cites: `prompt-turn.mdx:614`->`641`, `108-119`->`133-144`, `session-delete.mdx:89`->`90` (`--fix` does not touch code) | S-v1-0 |
| v1 `validation.py:5-7`, `protocol.py:61-62` | "three envelopes/dicts" -> four (`proxyMethods`); optional unit test that `set(load_meta())` matches the expected key set | S-v1-0 |
| v1 `test_session_capabilities.py:459` | Drop "(unstable)" | S-v1-3 |
| v1/v2 `_helpers.py` permission choice | C4 | S-X1 |
| v1 `connected_agent` | Opt-out of auto-`authenticate` (AUTH-007) | S-v1-7 |
| v1 `_base.py` | Unknown session -> `-32002`+data; no load/resume upsert; pre-init gate **with a `_tck/*` exemption** (`tests/common/test_harness.py:196,218,264` call probes before init); cursor validation; archive handlers | S-v1-1/2/4/6 |
| v2 `protocol.py:76,107` | `TOOL_CALL_STATUS += paused`, `TOOL_CALL_CONTENT_TYPE += session` (**must land in re-vendor**) | S-v2-0 |
| v2 `VENDORED.md` step 5, `protocol.py:27` | Root layout `Agent/Client/ProtocolLevel/Proxy`; version `2.0.0-alpha.14` | S-v2-0 |
| v2 `protocol.py:129-132,193` | `load_meta`/`KNOWN_METHODS` docstrings ("three") | S-v2-0 |
| v2 `_helpers.py:415-417` `_route_from_list` | **Bug:** stops on `nextCursor: ""`; break only on `None`/non-str | S-v2-12 |
| v2 `test_enums.py:118-121` | **Bug:** iterates a chunk's single `content` object; check `content.type` directly. Docstring `:3-4` closed-site list | S-v2-5 |
| v2 `validation.py` | Array path -> one issue; `_is_valid_request_id` null only on error; request-id check; docstrings `:8-13,202,224,256,491` | S-v2-1, S-v2-2 |
| v2 `_helpers.py` | `hold_permission` strict mode; "serialize prompts" docstring; stale line cites (`:864,314,891,1004-1007,124,993,1000-1002,1098-1100`); `:688-689` "never send a second initialize"; batch docstrings (`:118,162,531,639,796`) | S-v2-6, S-v2-7, S-v2-4, S-v2-1 |
| v2 test docstrings | `test_initialize.py:4-8`, `test_prompt_capabilities.py:11-12`, `test_session_capabilities.py` "unstable systemPrompt", `test_diagnostics.py:17`, `test_cancel.py` line refs, `test_transport.py`, `test_jsonrpc.py:1-13` | the owning area slice |
| v2 fixtures | `answers_notifications.py`, `pushes_status_and_answers_notifications.py` null-id result (V2-D30); `_base.py` cascade (`_error(data=)`, init gating/retry/repeat, delete gating on `session.delete`, fork `-32002`, config validation + `config_option_update`, content rejection, cursor/relative cwd, adddirs, MCP transport, `session_info_update` on resume, delete/archive cancel active); `AsksPermissionAgent` `$/cancel_request` on cancel and close; `pushes_status_notifications.py` sets its flag only on a successful init | per area |
| v2 `tests/v2/test_cli.py:124-130` | `_ADVISORY_IDS` lists INFORMATIONAL BATCH-205..208 (moot once retired) | S-v2-1 |
| `cross-check/summary.py:23`, `cross-check/tests/test_summary.py` | Synthetic `ACP-BATCH-201` sample ids (hygiene) | S-XC |
| `src/tck/common/report.py:72-87` | Optional: neutralise terminal control sequences when printing agent text (`security.mdx:26`). Maintenance idea, not conformance | follow-up |

## 7. Cross-check impact (`cross-check/run.sh:153-157`; `--expect` is MANDATORY-only)

| Agent | Predicted change | Basis |
|---|---|---|
| `testy` (v1), `echo_agent` (v1) | `--expect` lines unchanged. The new v1 rows are ADVISORY/CAPABILITY, except PLAN-001 (vacuous) and the CLIENTCAP-007 extension (neither agent sends `session` content). Expect ADVISORY FAILs on `echo_agent` for ERROR-003 (no `data.sessionId` helper in Python) and ERROR-005 (plain Python v1 does not gate) | v1-err |
| `python_v2_agent` (rc2) | **Remove** `ACP-BATCH-201,ACP-BATCH-202,ACP-JSONRPC-001,ACP-JSONRPC-003` (their batch halves are gone). **Likely add** (hypothesis, from the SDK HEAD reading, not rc2): `ACP-INIT-212` (rejects a repeat `initialize`) and `ACP-INIT-214` (pydantic validates before reading the version). Add `ACP-BATCH-209` only if V2-D3 = MANDATORY (rc2 crashes). Unknown: ERROR-202, CANCEL-210/211, AUTH-201 | v2-tr, v2-init |
| `testy_v2` (Rust HEAD) | Mostly stays `=`, since Rust implements batch rejection, INIT-209..214 and ignores unknown cancel ids. **But** `run.sh:127-133` documents that testy exits right after rejecting `initialize`. That predicts FAIL or flakiness on **`ACP-INIT-209` (post-failure legs) and `ACP-INIT-211`** (retry). Add them to `--expect-flaky` or `--expect` after a run. Hypothesis: the current suite may already show testy_v2 FAILing BATCH-202/JSONRPC-003 (Rust replies `-32600` to a notification-only array) | v2-tr, v2-init |

Every prediction is a hypothesis. S-XC must run `cross-check/run.sh` and set the lines from observed results. It must also update the explanatory comments at `run.sh:134-147`.

## 8. Slice plan (single-worker; one slice = one commit; `uv run pytest` green after each)

**S-v1-0: v1 re-vendor (alone).**
1. With the pin still at beac4ba, run `uv run --package spec-tracker spec-impact beac4ba96190018e9f6d82e148ff275084c5aa3e 3961af94fa62d2386d993cadf1afc8b146fc799a --version v1 --spec-repo <checkout> --fix`.
2. Hand-fix every row in §1 marked "hand cite", plus the non-mdx JSONRPC-001 Rust path. Leave INFO-UNKNOWNSESSION-001's `error.mdx:6` as written: S-v1-1 retires the row.
3. Copy `schema.unstable.json` and `meta.unstable.json`. Bump `SCHEMA_REVISION` and `VENDORED.md`.
4. Re-case the map sections (§5) and fix the stale comment cites and docstrings (§6, S-v1-0 rows).
5. No fixture or test change is forced (195/195 verified in `v1-sch`). Run `spec-tracker/tests` with `--spec-repo`.

**S-X1: permission choice by kind + policy hook (v1+v2)** [C4]. Do it early: it is an operator-safety hazard independent of the spec.

| Slice | Content | Decisions |
|---|---|---|
| S-v1-1 | Retire INFO-UNKNOWNSESSION-001; ERROR-003, ERROR-004; INFO-PARSE/INVALIDREQ text; cite adds (JSONRPC-002/004, ERROR-001/002); `_base.py` unknown-session code + no upsert; fixtures `unknown_session_wrong_code.py`, `load_upserts_unknown_session.py`; `test_informational.py` docstring; map: error.mdx core | V1-D1, D2, D5, C9 |
| S-v1-2 | ERROR-005 (+ base pre-init gate with `_tck/*` exemption), ERROR-006, ERROR-007, ERROR-008; fixtures | V1-D3, D4 |
| S-v1-3 | CLOSE-003, SESSION-006 (+ `_mcp_stub.py` canary), SYSPROMPT-001..003 text, session-setup ledger | V1-D6, D7, C6 |
| S-v1-4 | LIST-003 (+ base cursor check), DELETE-003 `-32002` handling, list/delete ledger | V1-D8, D9 |
| S-v1-5 | PROMPT-003 text; CLIENTCAP-007 extension + fixture; PLAN-001/002 (+ `plan:{}` connection, `conforming_full` plan emission); PERM-001/002 + fixtures | V1-D10..D12; needs S-X1 |
| S-v1-6 | ARCHIVE-001..006 (+ base handlers, `conforming_full` advertises archive and `archived` flag) | C1 |
| S-v1-7 | AUTH-007/008 (+ `connected_agent` auto-auth opt-out, fixtures) | C1, V1-D18 |
| S-v1-9 | Remaining v1 ledger (initialization, prompt-turn, overview/ext/transports, config, security, tools, schema L1/L2, deferred-method entries), transports `reason` | C6, V1-D13, D14, D17 |
| S-v1-11 (optional) | TITLE-001/002, SESSIONSTATUS-001/002, ARCHIVE-007 | C1 |

**S-v2-0: v2 re-vendor (alone).**
1. Run `spec-impact ... --version v2 --fix` with the pin still at beac4ba.
2. Make every §2a hand fix (dangling pointers, the silent `#/anyOf/2|3` hazard, deleted-line cites, `meta.unstable.json` lines, `STATE-203` pointer, `PROMPT-205`/`FORK` repoints, and the `test_extensibility.py:218` docstring pointer).
3. Copy the schema and meta files and bump the pin. Update the `VENDORED.md` root layout and version, and `protocol.py:27`.
4. Add `paused` and `session` to the `protocol.py` enum sets.
5. Re-case the map sections.
6. Expected: only the pointer test and `test_enum_sets_match_the_schema` were red before these fixes (`v2-sch`). No fixture changes.

| Slice | Content | Decisions / deps |
|---|---|---|
| S-X2 | `_meta` key rename, v1+v2 (`test_extensibility.py`, v2 `test_cancel.py:326`/`_helpers.py:926-927`), optional probe rename + CLAUDE.md | C3 (domain from user) |
| S-X3 | Hint-aware null validation, v1+v2 (`validation.py` carve-out + docstrings, AUTH-006 text, unit tests) | C2; after S-v2-0 |
| S-X4 | Auth hazards: embedded-login timeout SKIP, logout ordering, docs (v1+v2) | C5 |
| S-v2-1 | Batch removal: retire BATCH-201..208 and INFO-BATCH-201/202; BATCH-209; TRANSPORT rename/text, TRANSPORT-203; JSONRPC-001/003/005 batch halves; SHUTDOWN-201; STDERR docstrings; `validation.py` array path; `test_batch.py` rewrite; fixtures (`rejects_batch` deleted, `crashes_on_batch`, `emits_batch_updates` inverted, `pushes_status_*`, new `ignores_batch`/`answers_batch_with_array`); `test_validation.py:29-48` inverted; map transports | V2-D1, D2, D3, D25 |
| S-v2-2 | Envelope: JSONRPC-002 null-on-error + request-id validation; retire JSONRPC-004 -> JSONRPC-201; JSONRPC-202; EXT-001 text; null-id fixtures; `core_defs`; V2-D23 pointer guard | M5, V2-D8, D23, D30 |
| S-v2-3 | Unknown session: retire INFO-UNKNOWNSESSION-001; ERROR-201 (+ set_config_option sub-test), RESUME-211, shared `-32002`+data helper; ERROR-202/203/204; ERROR-001/INFO-PARSE/INVALIDREQ text; `_base._error(data=)`, prompt/resume codes, delete gating; map error.mdx core | M1, V2-D4 |
| S-v2-4 | INIT-209..214; `_base` init gate/retry/repeat window; `pushes_status_notifications` flag; `starts_session_after_mismatch` {207,209}; init docstrings | V2-D7 |
| S-v2-5 | EXT-203 retier; META-202/203 (204 later); ENUM-201 sites + chunk loop bug; optional ENUM-204; `test_enums` docstring | V2-D5, D19, D20, D21 |
| S-v2-6 | Cancellation: strict CANCEL-209 (`run_prompt` hold mode); CANCEL-210..213; CLOSE-205; retire INFO-CANCEL-202; CANCEL-204/205, INFO-CANCEL-201 text; `AsksPermissionAgent` fixes; new fixtures; map cancellation.mdx core | M2, M20, V2-D16; needs S-X1 |
| S-v2-7 | Prompt lifecycle: retire PROMPT-208 (+ ledger, `responds_after_idle.py`); INFO-CONCURRENT-201; PROMPT-209 + CANCEL-214 (shared scenario); optional PROMPT-210; `run_prompt` H1 + docstrings; map Message IDs | M8, V2-D17, D24 |
| S-v2-8 | Content: PROMPT-211, PROMPTCAP-201 (runtime negative gate), PROMPT-206 text, PROMPTCAP-001..003 cite adds; `_base._prompt_rejection`; map content.mdx core | M4, V2-D18 |
| S-v2-9 | Background work: STATE-206..208 (+ fixtures) | V2-D17 (scope) |
| S-v2-10 | Session lifecycle/close/initial state: SESSION-204, 206-208; CLOSE-204 text, CLOSE-206, 207; ADDDIRS-203; MCP-201 text, MCP-203/204/205 | V2-D9, D10; after S-v2-6 (close path) |
| S-v2-11 | Resume: RESUME-210, 212-214, 216 (215 optional); CONFIG-203 shape-only; RESUME-201 text; `_base` `session_info_update` | M7, V2-D9, D27; after S-v2-9 (RESUME-213) |
| S-v2-12 | List/delete/fork: `_route_from_list` bug; LIST-203 text/test; LIST-205/206; DELETE-201/202/203 changes; DELETE-204/205; FORK-202 rider; FORK-203 (204 optional) | V2-D11, D12; after S-v2-3 (helper) |
| S-v2-13 | Config/commands: CONFIG-201/202/204 text; CONFIG-207..212; COMMANDS-201; validate only `configOptions` items; `_base` validation + `config_option_update` | V2-D13, D14, M12 |
| S-v2-14 | Auth: AUTH-201 retier; AUTH-202 text; AUTH-204 tightening; AUTH-208; AUTH-209; cite adds; fixtures (`duplicate_method_id` now NOT CONFORMANT) | V2-D6, D15, C1 |
| S-v2-15 | Tool calls: PERM-202/203 (decline-by-`cancelled` mode); PATCH-208/209 refinements; PATCH-210..212 (patch-state tracker) | V2-D19; needs S-X1 |
| S-v2-16 | Archive: ARCHIVE-201..207 (+ `_base` support) | C1 |
| S-v2-17 | Remaining v2 ledger (transports, extensibility, init, auth/elicitation, security/content, tool-calls, deferred methods), map leftovers | C6, D28 |
| S-v2-18 (optional) | SESSIONSTATUS-201..203, TITLE-201..203; deferred DIFF/PLAN/PATCH-213/214 | C1, D19 |
| S-XC | Cross-check: run, set `--expect`/`--expect-flaky`, update comments, `summary.py` sample ids | §7, V2-D31 |

**Order.** v1 goes first, because it is smaller and proves the procedure: S-v1-0 -> S-X1 -> S-v1-1..7 -> S-v1-9. Then v2: S-v2-0 -> S-X2, S-X3, S-X4 -> S-v2-1..17 -> optional slices -> S-XC.

**Shared baselines.** Every slice that changes `tests/fixtures/agents/v{1,2}/_base.py` shifts many `test_cli.py` exact sets. Each such slice must run the full `uv run pytest`, not just a `-k` subset (`v2-cc` closing note, `v1-err` testability).

**Decisions to settle before work starts.** Ask the user for C1, C3 (domain), C4, C6, V2-D1, V2-D2 and V2-D3 before S-v1-1. S-v1-0 and S-v2-0 need no decision.

## Open questions

- C3 needs a project-controlled reverse-DNS domain from the user.
- Cross-check predictions (§7) are unverified until S-XC runs. The Python checkout `pull --ff-only` failed for two researchers (`v2-tr`, `v2-init`), so freshness of the Python SDK reading is uncertain.
- `v2-ss` asks whether fork's own `configOptions`/`availableCommands` presence (`session-setup.mdx:108`) deserves a FORK row. No report proposed one; it is a candidate for S-v2-12 if wanted.
- Out of scope here: whether `auth/status_update` sent without `auth.status` is a violation (the spec is silent; no row recommended by `v1-init`, `v2-sch`, `v2-ae`).
