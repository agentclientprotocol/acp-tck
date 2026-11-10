# v2 impact audit: `docs/protocol/v2/draft/transports.mdx` (beac4ba -> 3961af9)

**Sources checked:** agent-client-protocol @ `3961af94fa62` (target) vs `beac4ba96190` (base), read via `git show`/`git diff`, not checked out; acp-rust-sdk @ `e75d6f19fabb` (2026-11-09, `pull --ff-only` OK); acp-python-sdk @ `8a9940744d0a` (= `1.0.0-2-g8a99407`, 2026-11-09). `pull --ff-only` failed with "Cannot fast-forward to multiple branches", but after `git fetch origin`, HEAD == `origin/main`, so the checkout is current. The cross-check pin `agent-client-protocol==1.0.0rc2` was also read at tag `1.0.0rc2`. acp-tck @ `200baba` (working tree).
**Confidence:** high on the wire facts and the blast radius (I read the doc, the schema root, both SDKs and every TCK file that mentions batches). Medium on the two tier calls flagged DECISION NEEDED, because the spec's receiver clause carries no RFC 2119 keyword.

## Answer

v2 dropped JSON-RPC batching. `transports.mdx:65-67 @ 3961af94fa62` says "Senders **MUST NOT** send a JSON array of messages, and receivers reject one with a single `-32600` (Invalid Request) response with `id: null`". The schema root `anyOf` went from 7 entries to 4: Agent, Client, ProtocolLevel, Proxy. All four `*BatchCall`/`*BatchResponse` entries are gone.

What this means for the registry:
- Every `ACP-BATCH-201..208` and `ACP-INFO-BATCH-201/202` row should be **retired**. Two of them are *inverted* by the change:
  - BATCH-202: a notification-only array used to need silence. It now needs the `-32600` reply.
  - BATCH-203: per-entry errors and siblings still running. Now the whole array gets one error and no element runs.
- Replace them with:
  - one new receiver row, **ACP-BATCH-209**: any array, empty or not, gets exactly one `-32600`/`id: null` object and no element is processed. Tier: DECISION NEEDED, I recommend ADVISORY, because the receiver clause has no keyword.
  - the sender MUST NOT, folded into the existing MANDATORY stdout-framing row (`ACP-TRANSPORT-201`). That row's text goes back to v1's "single JSON-RPC object per line", so I recommend renaming it to `ACP-TRANSPORT-001` (DECISION NEEDED).
- The new "Shutdown" section turns `ACP-SHUTDOWN-001`'s justification into a real SHOULD. Text and citation change; a fresh id is a DECISION NEEDED.
- The new "Message timing", "Message order" and "Custom transports" text is client-side, unobservable on stdio, or out of scope. It goes to the ledger, not new rows.
- Several citations no longer resolve and will break `tests/v2/test_registry.py`: `#/anyOf/3/items`, `#/anyOf/{2..5}/minItems`, `#/anyOf/4/items`. Two others still resolve but now point at the wrong thing, so the pointer test will *not* catch them: `#/anyOf/2` and `#/anyOf/3` now mean ProtocolLevel and Proxy.
- The Rust SDK already implements the new rule exactly. The Python SDK 1.0.0 handles only `[]` correctly and silently ignores non-empty arrays. The pinned rc2 crashes on any array.

## Summary table

| id | classification | note |
|----|----------------|------|
| ACP-BATCH-201 | **retired** (superseded by new ACP-BATCH-209) | `[]` behaviour is unchanged, but its MUST basis ("batch MUST be an array with at least one value", base :69) is gone. The rule now covers every array, so per the id convention it gets a fresh id. Pointers `#/anyOf/{2,3,4,5}/minItems` no longer resolve. |
| ACP-BATCH-202 | **retired (inverted)** | A notification-only array now gets one `-32600` reply, not silence. The "no reply to a notification" part survives in ACP-JSONRPC-003. |
| ACP-BATCH-203 | **retired (inverted)** | No per-entry errors. The whole array is rejected once and siblings must not run. |
| ACP-BATCH-204 | **retired** | There are no response arrays anymore. |
| ACP-BATCH-205 | **retired** | The response order inside an array no longer exists. |
| ACP-BATCH-206 | **retired** | Concurrent processing of batch entries no longer exists. |
| ACP-BATCH-207 | **retired (inverted)** | The agent MAY batch → MUST NOT. Covered by changed ACP-TRANSPORT-201/-001. Pointer `#/anyOf/4/items` no longer resolves. |
| ACP-BATCH-208 | **retired** | The lifecycle-batching SHOULD NOT is moot. |
| ACP-INFO-BATCH-201 | **retired** | An invalid-JSON line is just a parse error now. Covered by ACP-INFO-PARSE-001; that row's "error.mdx is a stub" text is stale, an open question for the error.mdx owner. |
| ACP-INFO-BATCH-202 | **retired** | A mixed call/response array is just an array, so it falls under ACP-BATCH-209's probe matrix. Its pointers now resolve to ProtocolLevel/Proxy, i.e. the wrong objects. |
| ACP-TRANSPORT-201 | **changed text** (MANDATORY kept). **DECISION NEEDED**: rename to `ACP-TRANSPORT-001` | Drop the array branch. A JSON array on stdout is now non-conformant. Repoint the citation (`#/anyOf/2`/`#/anyOf/3` silently mean the wrong objects). |
| ACP-TRANSPORT-002 | unchanged | `transports.mdx:6`; same line, same text. |
| ACP-TRANSPORT-203 | **changed text** (minor; tier kept) | Drop "a batch array is therefore serialised on one line too". Citation :25 → :21. |
| ACP-JSONRPC-001 | **changed text + citation** | Drop the batch clause. Cite `transports.mdx:76-81` (past the end of the file now, 73 lines) and `#/anyOf/3/items` (does not resolve) → overview + `#/$defs/AgentResponse`. Delete its batch test. |
| ACP-JSONRPC-002 | **citation-only, must be repointed** (not this doc, but hit by root `anyOf`) | `#/anyOf/3/items` no longer resolves → `#/$defs/AgentResponse`. |
| ACP-JSONRPC-003 | **changed text + citation** | Drop "including a notification inside a batch" and the `transports.mdx:76-79` citation. Keep overview. |
| ACP-JSONRPC-005 | **changed text** (not cited here, but tested via batch) | "invalid or empty batch" → "a rejected JSON array". Rebind its batch evidence to the BATCH-209 probe's follow-up request. |
| ACP-CANCEL-205 | **citation-only (Needs review)** | Remove `transports.mdx:78-79`; that text no longer exists anywhere. Overview :197 → :227. The schema pointers still resolve. |
| ACP-SHUTDOWN-001 | **changed text/citation; DECISION NEEDED: fresh id `ACP-SHUTDOWN-201`** (ADVISORY) | The spec now has a real SHOULD ("SHOULD exit once it has finished or stopped its work"). Citation :41 → :43. The "no stdin-EOF MUST, only the mermaid step" rationale is stale. |
| ACP-STDERR-001 | citation-only | :26 → :22, same text. `--fix` will remap it. |
| **ACP-BATCH-209** (new) | **new**, tier DECISION NEEDED (recommend ADVISORY) | Any JSON array on stdin (empty, request-only, notification-only, invalid elements, mixed) gets exactly one `-32600` object with `id: null`, and no element is processed. |
| ledger L1-L7 | **new non-requirements** | Message timing (client MUST), message order (transport/client MUSTs), connection-end request failure, sessions inactive at EOF, custom transports, stdio SHOULD, client MUST NOT send arrays. |

## Requirements

| # | Requirement (target text) | Tier | Citation |
|---|---|---|---|
| R1 | Each stdio message is a single JSON-RPC request, notification, or response object | MUST (with R2, R3) | `docs/protocol/v2/draft/transports.mdx:20 @ 3961af94fa62` |
| R2 | Agent MUST NOT write anything to stdout that is not a valid ACP message | MUST | `transports.mdx:23` |
| R3 | Senders MUST NOT send a JSON array of messages | MUST (agent as sender) | `transports.mdx:67`; `overview.mdx:21`; root `anyOf` has no array branch (`schema/v2/schema.unstable.json#/anyOf`) |
| R4 | Receivers reject an array with a single `-32600` response with `id: null` | no keyword (indicative) → ADVISORY recommended, DECISION NEEDED | `transports.mdx:67`; restated without keyword at `docs/rfds/v2/overview.mdx:70`, `docs/protocol/v2/migration.mdx:32,896` |
| R5 | Messages newline-delimited, MUST NOT contain embedded newlines | MUST | `transports.mdx:21` |
| R6 | JSON-RPC messages MUST be UTF-8 | MUST | `transports.mdx:6` |
| R7 | Agent MAY write UTF-8 logging to stderr | MAY | `transports.mdx:22` |
| R8 | On stdin EOF the agent treats the connection as ended, its sessions stop being active, and it SHOULD exit once it has finished or stopped its work | SHOULD | `transports.mdx:43` |
| R9 | Client MAY SIGTERM then SIGKILL if no exit within a reasonable time | MAY (client) | `transports.mdx:43` |
| R10 | At connection end, either side treats its unanswered requests as failed | indicative, unobservable | `transports.mdx:45` |
| R11 | After `initialize`, agents MAY send requests/notifications at any time; clients MUST handle them independently | MAY (agent) / MUST (client) | `transports.mdx:49-53` |
| R12 | That permission does not override capability or lifecycle rules (session-scoped messages need a valid session) | (restates other docs) | `transports.mdx:55-57` |
| R13 | Transports MUST deliver in send order; receivers MUST apply a session's `session/update`s in receipt order | MUST (transport / client) | `transports.mdx:61-63` |
| R14 | Custom transports MUST preserve format, order and lifecycle; SHOULD document; MAY add their own requirements | MUST/SHOULD/MAY (out of scope) | `transports.mdx:71-73` |
| R15 | Agents and clients SHOULD support stdio | SHOULD | `transports.mdx:10` |

## Details

### Wire change (B1)

- Base `transports.mdx:57-97` ("JSON-RPC Batch Messages") is fully removed. The target replacement is `transports.mdx:65-67` ("No batches").
- Stdio bullet: base :23-24 "...responses, or batch arrays" becomes target :20 "Each message is a single JSON-RPC request, notification, or response object".
- Schema root `anyOf`:
  - base: `[Agent, Client, AgentBatchCall, AgentBatchResponse, ClientBatchCall, ClientBatchResponse, ProtocolLevel]`
  - target: `[Agent, Client, ProtocolLevel, Proxy]`

  I resolved each pointer against the target schema:

  | Pointer | Target result |
  |---|---|
  | `#/anyOf/2` | ProtocolLevel |
  | `#/anyOf/3` | Proxy |
  | `#/anyOf/2/minItems`, `#/anyOf/3/minItems`, `#/anyOf/3/items` | KeyError |
  | `#/anyOf/4/*`, `#/anyOf/5/*` | IndexError |
  | `#/$defs/ClientNotification/properties/params/anyOf/0/anyOf/0` | still CancelSessionNotification |
  | `#/$defs/AgentResponse` | exists, the `{Result, Error}` anyOf |

- Intent: `docs/rfds/v2/overview.mdx:70` says "Do not use JSON-RPC 2.0 batches ... receivers reject an array with `-32600`, as MCP does since 2025-06-18"; changelog `:136` says "2026-10-29: Dropped JSON-RPC batches from v2, following MCP". `schema/v2/CHANGELOG.md:42` alpha.11 is #2625 (commit `bf529a96`). `docs/rfds/v2/terminal-output.mdx:198` removed a batch-ordering rule for the same reason.
- Pre-init interaction: an array arriving before `initialize` is still an array. The transports rule is unconditional, and `initialization.mdx:90`/`error.mdx:60` reject pre-init requests with `-32600` anyway. The Rust SDK tests exactly this case (see below).

### Proposed rows (text for the programmer)

**ACP-TRANSPORT-201 → (recommended) ACP-TRANSPORT-001**, MANDATORY.
- Text: "Every line the agent writes to stdout is a single valid JSON-RPC 2.0 message object; a JSON array (empty or not) is non-conformant."
- Citation: `docs/protocol/v2/draft/transports.mdx:20,23,67; schema/v2/schema.unstable.json#/anyOf (Agent/Client/ProtocolLevel/Proxy, all type: object)`.
- Why rename: v1's `ACP-TRANSPORT-001` is "Every line the agent writes to stdout is a single valid JSON-RPC 2.0 message." (`src/tck/v1/requirements.py:29-33`), the same tier. The v2 registry docstring says "A v1 id is reused bare only when the v2 requirement is truly the *same* one" (`src/tck/v2/requirements.py:7-11`). The 201 id existed only because v2 widened the rule to arrays (`test_transport.py:3-6`).
- **DECISION NEEDED**:
  - Option A (recommended): rename, so the registry follows its own convention.
  - Option B: keep 201 with the changed text. Less churn: `tests/v2/test_cli.py` names `ACP-TRANSPORT-201` in at least 8 places (`:38, :963, :1032, :1133, :1192, :1365, :1419, :1471, :1518, :1568`).
- Test: `test_transport.py:48-70`. Replace the `list` branch (`:62-68`) with a failure ("JSON array on stdout: ACP does not use batches"). Rename the test, since it is no longer `..._or_batch`.
- Coverage gap: this test sees only `_drive_full_exchange` traffic. To catch an agent that answers an array *probe* with an array, the BATCH-209 test must assert that its reply is a `dict`. That covers it in substance, but under the ADVISORY id if the recommendation is taken. Option: also mark the BATCH-209 test with this id and assert there that no received line is a list. Then "agent sent an array" is MANDATORY wherever it happens. I recommend this double marker.

**ACP-BATCH-209 (new)**. Tier **DECISION NEEDED**, recommend ADVISORY.
- Text: "Any JSON array the agent receives on stdin -- empty, request-only, notification-only, containing non-object elements, or mixing call- and response-shaped elements -- is rejected with exactly one Invalid Request (`-32600`) error object whose `id` is `null`; no element is processed (no response carries an element's `id`)."
- Citation: `docs/protocol/v2/draft/transports.mdx:65-67; docs/protocol/v2/draft/overview.mdx:21`. Do not cite the RFD as the requirement; it is design intent.
- Tier reasoning:
  - The sender clause is bold **MUST NOT**. The receiver clause ("receivers reject one with ...") has no keyword, and the 2026-10-27 pass bolded every normative keyword (`77926921`).
  - The registry precedent for keyword-less rules is ADVISORY: `ACP-BATCH-203` (`requirements.py:817-826`), citing v1 `ACP-JSONRPC-005`.
  - Arguments for MANDATORY: the sentence is the section's only receiver rule and is stated as definitional. `error.mdx:29` lists `-32600` for "not a valid request object". The Rust reference treats it as hard behaviour.
  - Arguments against: no MUST anywhere (overview:21, RFD:70 and migration:32/896 are all indicative), and Python SDK 1.0.0 does not comply.
  - Consequence of ADVISORY: a crash on an array (`crashes_on_batch.py`) no longer makes a run NOT CONFORMANT, except through the TRANSPORT double marker (a crash writes no array, so that marker does not catch it). If the orchestrator wants "crash on array" to block, the tier must be MANDATORY. A middle option is to ask upstream to bold a MUST.
- Probe matrix: one fresh `v2_only_agent` per case, as today. Each gets one reply object `{"id": null, "error": {"code": -32600}}`, then a quiet period with no further reply line (`first_response_within`):
  - `[]`
  - `[{"jsonrpc":"2.0","method":"_tck/notify_only"}]` (notification-only; this is the inverted BATCH-202)
  - `[{request id "tck-batch-a"}, {request id "tck-batch-b"}]` using `session/list` or `_tck/does_not_exist`. Assert that neither id is ever answered (the inverted BATCH-203/204).
  - `[17, true, null]`
  - the mixed call/response array from today's INFO-BATCH-202 probe

  The same test (or one of them) then sends an ordinary request and expects an ordinary reply. That is `ACP-JSONRPC-005`'s evidence, keeping the current marker pairing. Matches Rust `tests/jsonrpc_batch.rs:113-158`, which uses the same five shapes plus "connection keeps serving".
- Optional extra case: `[initialize]` as the very first line → `-32600`/`id:null`, then a plain `initialize` succeeds. Rust tests this at `tests/jsonrpc_batch.rs:162-176,210-225`. It needs `connected_agent(handshake=False)`, and it interacts with INIT gating rows, so check with the initialization owner first.
- Probe legitimacy: the TCK, as sender, deliberately breaks "Senders MUST NOT send a JSON array" (`:67`) and "client MUST NOT write ... not a valid ACP message" (`:24`). The receiver clause exists precisely for that input, which is the same justification `test_batch.py:25-27` already gives. Update its line citations to `:24`, `:67`.
- Suggested fixtures, see the blast-radius section.

**ACP-SHUTDOWN-001 → (DECISION NEEDED) ACP-SHUTDOWN-201**, ADVISORY.
- Text: "After the client closes stdin, the agent treats end of input as the end of the connection and exits on its own once it has finished or stopped its work, without needing SIGTERM/SIGKILL."
- Citation: `docs/protocol/v2/draft/transports.mdx:43`.
- Why a fresh id: v1's `ACP-SHUTDOWN-001` is INFORMATIONAL (`src/tck/v1/requirements.py:1004-1015`). v2's row is ADVISORY but claims "Re-cited from v1 unchanged" (`src/tck/v2/requirements.py:1779-1788`). That was already a tier mismatch under the id convention. v2 now has an explicit SHOULD, so ADVISORY is well-founded but differs from v1, and the convention says the id should be fresh.
- Option: keep the id and fix only the text (less churn: `test_cli.py:142`, `test_registry` lists).
- Test: `test_diagnostics.py:45-58` still matches, because it closes stdin with no work in flight, so "finished" holds immediately. Update the docstring (citation `:41` → `:43`, drop the "no dedicated shutdown" rationale) and the failure message ("the spec does not mandate shutdown timing" → "SHOULD exit once it has finished or stopped its work").
- Optional extension, same id: close stdin mid-turn (`--cancel-prompt`/`__hang__`) and expect an exit within `--close-grace`. The spec bounds this only by "reasonable time" (client side), so keep it ADVISORY and lenient. I do not recommend making it a new row.

**ACP-TRANSPORT-203**. Text: drop the clause "-- a batch array is therefore serialised on one line too". Citation `transports.mdx:21`. Test `test_transport.py:85-119` is unchanged apart from the docstring (`:88`) and comment (`:101`).

**ACP-JSONRPC-001**
- Text: "A response's `id` echoes the request `id` exactly (integer and string ids), whether it is a result or an error."
- Citation: `docs/protocol/v2/draft/overview.mdx:15-17` (ids are string or integer, never null; `id: null` only when undeterminable) and `:233` (envelope fields follow JSON-RPC 2.0), plus `schema/v2/schema.unstable.json#/$defs/AgentResponse`. Remove `transports.mdx:76-81` and `#/anyOf/3/items`.
- Tests: delete `test_batch.py:196-227`. `test_jsonrpc.py:36` remains the sole evidence. Rewrite the `test_jsonrpc.py:1-13` module docstring, which describes the "batch half".
- The overview.mdx owner may also touch this row (the `RequestId` change); coordinate.

**ACP-JSONRPC-002**. Repoint `#/anyOf/3/items` → `schema/v2/schema.unstable.json#/$defs/AgentResponse`. Line `overview.mdx:195-196` → `:225-226`. Meaning is unchanged.

**ACP-JSONRPC-003**
- Text: "Notifications never receive a response, success or error. Messages the agent itself initiates (they carry `method`) are not responses."
- Citation: `docs/protocol/v2/draft/overview.mdx:227`.
- Remove the marker from the deleted `test_batch.py:74-87`.
- Note: an array holding only notifications now *does* get a reply. That reply answers the invalid array, not the notification, so JSONRPC-003 must not be bound to the BATCH-209 notification-only case.

**ACP-JSONRPC-005**. Text "including an invalid or empty batch" → "including a rejected JSON array". Its citation `overview.mdx:191-197` is now `:221-229` (overview owner). Move its batch evidence from `test_batch.py:125-158` to the BATCH-209 follow-up request.

**ACP-CANCEL-205**. Remove `docs/protocol/v2/draft/transports.mdx:78-79`. Nothing in the target doc says it anymore, so `spec-impact --fix` cannot remap it; it lands in "Needs review". `overview.mdx:197` → `:227`. The schema pointers resolve unchanged. No test change, though the docstring of `test_cancel.py:295` mentions batch elements.

**ACP-STDERR-001**. Citation `transports.mdx:26` → `:22`. Also update the `transports.mdx:26` mentions in the `test_diagnostics.py:3,64` docstrings.

### Ledger entries (deliberate non-requirements)

| # | citation | statement | reason |
|---|---|---|---|
| L1 | `docs/protocol/v2/draft/transports.mdx:49-53 @ 3961af94fa62` | Clients MUST handle agent requests/notifications sent at any time after `initialize`, independently of awaited responses. | Client-side rule. The agent's MAY is permissive, so there is nothing to fail. The TCK's harness complies (`is_agent_initiated`/`next_reply_line`). |
| L2 | `transports.mdx:61` | Transports MUST deliver messages in send order. | Unobservable on stdio: a pipe is ordered by construction, and the TCK sees only one ordering. Custom transports are out of scope. |
| L3 | `transports.mdx:61-63` | Receivers MUST apply a session's `session/update` notifications in receipt order. | Client-side rule. The agent is the sender of `session/update`. |
| L4 | `transports.mdx:45` | When the connection ends, either side treats its unanswered requests as failed. | Unobservable: after EOF the agent has no channel left to show how it treats its own pending requests. |
| L5 | `transports.mdx:43` (first sentence) | On stdin EOF the agent's sessions stop being active. | Unobservable from a single-connection stdio client: the next connection is a new process, where "not active" holds by definition (`session-setup.mdx:49`). |
| L6 | `transports.mdx:10,71-73` | Agents SHOULD support stdio; custom transports MUST preserve format/order/lifecycle, SHOULD document, MAY add their own requirements. | Out of scope: the TCK drives stdio only, and an agent it can run already supports stdio. |
| L7 | `transports.mdx:67` (sender clause, client side), `:24` | Clients MUST NOT send JSON arrays or non-ACP lines to the agent. | Client-side rule the TCK deliberately breaks in its array/parse probes to exercise the receiver rule (ACP-BATCH-209, ACP-INFO-PARSE-001). Optional to record. |

Skip `transports.mdx:55-57` (R12). It restates capability and lifecycle rules owned by other docs and adds no new testable rule.

### spec-tracker map (`spec-tracker/maps/v2.toml:109-117`)

- The whole doc stays core, with no `sections` key, so there are no section addresses to update. The doc's new headings, all sentence-case and all covered: `stdio`, `stdio > Shutdown`, `Message timing`, `Message order`, `No batches`, `Custom transports`.
- `code`:
  - drop `src/tck/v2/conformance/test_batch.py` if the file is renamed or merged (keep it if BATCH-209 stays there);
  - add `src/tck/v2/conformance/test_diagnostics.py`, which owns SHUTDOWN/STDERR;
  - keep `src/tck/common/harness` (the `close()` ladder implements `:43`'s client MAY);
  - keep `src/tck/v2/validation.py`.
- `reason`: "stdio framing, shutdown, message timing and order, and the no-batches rule that every message exchange depends on".

### Blast radius (exact)

**`src/tck/v2/conformance/test_batch.py`**
- Delete `:56-71`, `:74-87`, `:90-122`, `:125-158`, `:161-227`, `:230-268`, `:271-311`.
- Replace them with the BATCH-209 probe test(s), reusing `v2_only_agent`, `next_reply_line`, `first_response_within`, `quiet_period` and `_probe_method`.
- Rewrite the module docstring (`:1-28`). Keep the `skip_if_version_mismatch` rationale: a v1-only agent still silently drops arrays.

**`src/tck/v2/validation.py`**
- Rewrite docstring point 1 (`:8-13`).
- Remove `_empty_batch_issue` (`:220-225`).
- In `validate_agent_message` (`:243-250`) and `validate_agent_response` (`:479-485`), replace the `list` branches with one issue for *any* list, e.g. "a JSON array is not an ACP message (v2 has no batches)", `schema_path="#/anyOf"`.
- Fix the error-message strings at `:256` and `:491` ("JSON object or a non-empty batch array" → "JSON object") and the docstrings at `:52`, `:229-231`, `:317`, `:467`.
- `tests/v2/test_validation.py:2,13,29-45` must be inverted.
- Recheck `VENDORED.md:37` (lists the batch branches) at refresh.
- The `protocol.py` method tables do not use root `anyOf` indexes (grep), so they self-update.

**`src/tck/common/harness`**: **no change**. It is not batch-aware: `transcript.py:72-78` `matches_id` is dict-only, and `process.py` has no list handling. `close()` (`process.py:323-`) already models `:43`.

**`src/tck/v2/conformance/_helpers.py`**
- Batch flattening appears at `:560-574` (`iter_messages`), `:577-586` (`is_response_line`), `:601-615` (`is_agent_initiated`) and `:962-973` (`run_prompt._handle_one`), plus docstrings at `:118`, `:162`, `:531`, `:639`, `:796` that cite `ACP-BATCH-207`.
- **Recommendation (programmer decision; it is not a protocol question):** keep the tolerant flattening, so a batching agent fails *only* the transport row and is not cascaded into every prompt row. Update the docstrings to say arrays are non-conformant (TRANSPORT row) and are flattened only so other rows can still be judged.
- One exception: `is_agent_initiated` treating an all-`method` array as "agent-initiated, skip it" would let the BATCH-209 probe skip past an array. Either make it return `False` for any list, or have the probe assert directly that no list line arrived (the TRANSPORT double marker above).
- `tests/v2/test_helpers.py:34-38` encodes the current classification and must follow whichever choice is made.

**Other conformance files (docstrings/comments citing BATCH-207; behaviour can stay tolerant)**: `test_enums.py:240-243`, `test_initialize.py:472-482`, `test_extensibility.py:248`, `test_cancel.py:295`, `test_session_capabilities.py:56,522`, `test_transport.py:1-12,49-70,88,101`, `test_jsonrpc.py:1-13,90-92`.

**Fixtures (`tests/fixtures/agents/v2/`)**

| Fixture | Change |
|---|---|
| `_base.py` (conforming baseline) | `_handle_batch` `:153-171`, `_handle_batch_entry` `:174-185`, `_batch_collector` `:116`, the `_write` buffering `:693-700` and docstring `:22-24` must change. Any list → `_write_line({"jsonrpc":"2.0","id":None,"error":{"code":-32600,...}})`; delete the collector. Keep the `_handle_batch` method name as the hook, since subclasses override it. |
| `rejects_batch.py` | Its "defect" is now exactly the conforming behaviour. **Delete**, along with `test_cli.py:1610-1633` (`test_rejects_batch_fails_batch_202_through_204_only`). |
| `crashes_on_batch.py` | Keep. Under the new suite it should FAIL exactly `{ACP-BATCH-209, ACP-JSONRPC-005}` (follow-up request in the same test). Update its docstring and `test_cli.py:1635-~1668`. If BATCH-209 is ADVISORY, the fixture's overall verdict becomes CONFORMANT; assert that explicitly so the tier choice is visible. |
| `emits_batch_updates.py` | **Inverted**: a positive control becomes a defect (MUST NOT). Expect FAIL of only the TRANSPORT row (201/001), provided `run_prompt` keeps flattening. Update its docstring and `test_cli.py:1890-1935` (`..._passes_everything` → `..._fails_transport_only`). |
| `pushes_status_notifications.py` | Labelled conforming, but its `_handle_batch` override (`:40-44`) pushes an array `[_STATUS, _STATUS]`, which is now a MUST NOT violation. Change it to push a single status object before the rejection. Update docstring `:4-10`. `test_cli.py:1793-1802` stays "passes everything". |
| `pushes_status_and_answers_notifications.py` | Docstring `:3-8`. The expected FAIL set drops `ACP-BATCH-202` and becomes `{ACP-JSONRPC-003, ACP-EXT-201}` (`test_cli.py:1811-~1826`). |
| `pushes_status_and_splits_batch_replies.py` | Its defect (splitting a reply array) no longer exists. **Repurpose** as "pushes status and answers an array's elements one per line instead of rejecting the array". It FAILs only BATCH-209 and proves skipping the agent's own notifications does not hide element processing. Otherwise delete it. Update `test_cli.py:1828-~1850`. |
| `custom_method_no_response.py` | Docstring `:11-12` only (the no-cascade-into-BATCH note). |
| `noisy_stderr_and_parse_error_reply.py` | `:37-39` calls `self._handle_batch`. It still works if `_base` keeps the hook name. `test_cli.py:2656` "fails nothing" should still hold; re-run to confirm. |
| **new** `ignores_batch.py` (suggested) | Python-SDK-1.0.0-like: answers `[]` with `-32600`/null but silently drops non-empty arrays. Should FAIL only BATCH-209. |
| **new** `answers_batch_with_array.py` (suggested) | The old `_base` behaviour, i.e. dispatch the elements and reply with an array. FAILs BATCH-209 and, through the double marker, the TRANSPORT row. |

**`tests/v2/test_cli.py`**
- Tier sets: `_MANDATORY_IDS` `:38` (TRANSPORT rename?), `:44-45`; `_ADVISORY_IDS` `:124-130` (note it currently lists BATCH-205..208, which the registry tiers INFORMATIONAL); `:142` SHUTDOWN; `_INFORMATIONAL_IDS` `:150-151`; `_ALWAYS_SKIPPED_IDS` `:161-176`. Add BATCH-209 to whichever tier is chosen.
- The fixture tests listed above.
- Check the `-k "batch"` scoping at `:1618` and the `crashes_on_batch` `-k`.
- Check `wrong_id_echo` at `:1741-1760`: its docstring mentions JSONRPC-001's batch test.

**`tests/v2/test_registry.py`**: the id lists at `:84-102`, `:179-180`, `:201-211`. The pointer test `:385` will fail on the unresolvable pointers listed above until they are repointed.

**`cross-check/run.sh`**
- `:141-144` comment and `:157` `--expect "python_v2_agent=ACP-BATCH-201,ACP-BATCH-202,ACP-INIT-003,ACP-INIT-202,ACP-INIT-205,ACP-INIT-206,ACP-JSONRPC-001,ACP-JSONRPC-003"`. Remove `ACP-BATCH-201,ACP-BATCH-202,ACP-JSONRPC-001,ACP-JSONRPC-003`. Add `ACP-BATCH-209` only if it is MANDATORY: the `--expect` sets are MANDATORY-only (`:145-146` comment), and rc2 still crashes, so it FAILs.
- `testy_v2=` (`:155`) should stay empty under the new suite, because Rust HEAD implements the rule.
- Hypothesis, not run: against the *current* suite, testy built from Rust HEAD should already FAIL `ACP-BATCH-202`/`ACP-JSONRPC-003`, because it replies `-32600` to a notification-only array (behaviour since rust-sdk `5887c72`, 2026-10-30). The informational cross-check job may already be red on this.
- `cross-check/summary.py:23` and `cross-check/tests/test_summary.py:127-227` use `ACP-BATCH-201` only as synthetic sample ids. They are not registry-checked, so it is optional to change them; do so for hygiene.

### Reference SDK behaviour

**Rust @ e75d6f1 — complies with the target exactly**
- `src/agent-client-protocol/src/jsonrpc/transport_actor.rs:26-33`: "An array, including an empty one, is one invalid request answered with a single error". `util.rs:230-237` builds `batch_not_supported()` as `-32600` with data.
- Unit test `transport_actor.rs:371-386` covers `[]`, `[1,2,3]`, a request array and a response array.
- Integration test `tests/jsonrpc_batch.rs:113-158` covers `[]`, `[1,2,3]`, two requests, notification-only and a response-shaped array. Each gets one object with `id: null` and `-32600`. No entry is dispatched, and the connection keeps serving.
- `[` (invalid JSON) → `-32700` (`transport_actor.rs:388-395`).
- Batched `initialize` is rejected and a retry accepted, for v1, v2 and the router (`tests/jsonrpc_batch.rs:162-176,210-225,230-249`).
- The rule applies to v1 connections too. Introduced in `5887c72 feat(acp)!: remove JSON-RPC batch support (#454)`.

**Python @ 8a99407 (1.0.0+2) — partial**
- `src/acp/_jsonrpc.py:18-24`: a non-empty dict passes, a non-empty list returns `None`, and anything else (including `[]`) raises `invalid_request()`.
- `src/acp/_transport.py:72-83`: an error becomes a single `{"id": null, "error": ...}` (`_jsonrpc.py:27-28`); `None` means `continue`, i.e. a non-empty array is **silently ignored**.
- So `[]` complies, and non-empty arrays get no reply, which would FAIL BATCH-209. The HTTP server answers a batch with HTTP 501 (`tests/http/test_http_server.py:72-78`); that is not stdio, so it is not relevant.
- Introduced in `fc545d6` (released in 1.0.0).

**Python 1.0.0rc2 (cross-check pin) — crashes**: `src/acp/connection.py:152-153 @ 1.0.0rc2` calls `message.get("method")` on whatever the transport returns, so a list raises `AttributeError`. This matches the cross-check note at `cross-check/run.sh:141-144`.

## Testability notes

- **TRANSPORT row**:
  - Observable on every stdout line. Conforming: only dict lines.
  - Non-conforming: any `list` line, including a spontaneous notification array (`emits_batch_updates.py`) or an array reply to an array probe.
  - Evidence: the full exchange, plus the BATCH-209 probe connections if the double marker is adopted.
- **BATCH-209**:
  - Conforming: exactly one reply line, a dict with `id` null and `error.code == -32600`, and no later reply within the quiet period.
  - Agent-initiated notifications and requests around it are skipped (`next_reply_line`). Arrays should *not* be skipped.
  - Non-conforming: silence (Python 1.0.0); a crash (`AgentExited`); per-element replies; a reply carrying an element's id; an array reply; a code other than `-32600`; a non-null id.
  - Whether a *notification* element was processed is unobservable for side-effect-free notifications. Assert only on request elements and on the reply count.
  - Race: none beyond the quiet-period length, same as today's no-reply checks.
- **SHUTDOWN**: Observable through `AgentProcess.exited_on_stdin_close`. Mid-work shutdown is observable only loosely ("reasonable time"), so keep it ADVISORY and lenient.
- **Unobservable**: L2-L5. Message timing (R11) is only a permission for the agent.

## Discrepancies

1. **SDKs vs spec**: Rust matches `transports.mdx:67` exactly. Python 1.0.0 silently ignores non-empty arrays (`_jsonrpc.py:22-23`, `_transport.py:80-81`), which contradicts "receivers reject one with a single `-32600`". Python rc2 crashes. The spec's receiver clause has no RFC 2119 keyword, so how severe the Python gap is depends on the tier decision.
2. **Spec keyword strength**: the receiver rule is never stated with MUST: `transports.mdx:67`, `overview.mdx:21`, `rfds/v2/overview.mdx:70` and `migration.mdx:32,896` are all indicative. Compare pre-init rejection, which is indicative in `initialization.mdx:90` but **MUST** in `error.mdx:60`. Batch rejection has no such MUST counterpart.
3. **Registry-internal, pre-existing**: v2 `ACP-SHUTDOWN-001` is ADVISORY while v1's is INFORMATIONAL, yet the v2 text says "Re-cited from v1 unchanged". That violates the registry's own id-reuse rule. `tests/v2/test_cli.py:124-130` lists BATCH-205..208 under `_ADVISORY_IDS`, while the registry tiers them INFORMATIONAL. That is moot once they are retired.
4. **Silent wrong citations**: `ACP-TRANSPORT-201` (`#/anyOf/2`, `#/anyOf/3`) and `ACP-INFO-BATCH-202` still resolve at target, but now point at ProtocolLevel and Proxy. `test_registry`'s pointer check will not flag them.

## Open questions

- **error.mdx owner**: `error.mdx` is now a real page (`:24-60 @ 3961af94fa62`).
  - `ACP-INFO-PARSE-001`/`ACP-INFO-INVALIDREQ-001` justify themselves with "error.mdx is still 'Documentation coming soon'", which is stale. The table gives `-32700`/`-32600`, but without MUST.
  - `error.mdx:44` makes unknown methods "**MUST** respond with `-32601`", while `ACP-JSONRPC-004` is ADVISORY "spec wording is still 'should'". Route to the error/extensibility auditor.
- **overview.mdx owner**: the JSONRPC-001/002/003/005 line remaps (`overview.mdx:15-21,221-233`) and the new `RequestId` never-null rule.
- **initialization.mdx owner**: `initialization.mdx:91` "Agents **MUST NOT** send requests or notifications" before init completes. That is the agent-side complement of transports' "Message timing" and is not covered here. Also, whether to add the `[initialize]`-as-first-line probe (Rust has it) belongs with the INIT gating rows.
- **Orchestrator decisions**: BATCH-209 tier (ADVISORY vs MANDATORY); TRANSPORT-201 → 001 rename; SHUTDOWN-001 → 201; whether `is_agent_initiated` stops skipping arrays or the probe asserts "no list line" (double marker).
- **cross-check**: consider bumping the Python pin from rc2 to 1.0.0, which moves `python_v2_agent` from crash to silent-ignore on arrays. That is a cross-check owner's call, not a spec question.
