# Do the TCK's v2 prose citations survive a move to the `docs/protocol/v2/draft/` tree?

**Sources checked:** agent-client-protocol @ `9af0e9f748db9f4cc4c410a7b212ead4f98ae78c` (2026-09-29, HEAD; `git pull --ff-only` was already up to date). I also compared against the TCK's pinned `SCHEMA_REVISION` `d8805733` and against `8f76d6c`, the revision the `prompt-lifecycle.mdx` line numbers actually match (see F1).
**Confidence:** high. Every cited line was mapped mechanically with a `difflib` line alignment (stable file at the pinned or matching revision against the draft file at HEAD), and each mapped line was read by eye.

## Answer

None of the TCK's v2 prose citations become category (iv): no cited normative sentence is changed or removed in the draft tree. The cited text is either identical at the same line (i), identical at a shifted line (ii), or reworded without a change in meaning (iii). The one exception is `migration.mdx`, which has **no** draft counterpart. Eight citation sites point into it. Five of those restate a MUST that the draft tree also states elsewhere, and the other three are now backed only by the unstable schema/meta files. Neither case changes a requirement.

The known drop ("Extension-specific capabilities belong in `_meta`", stable `initialization.mdx:116-117` becomes draft `:120`) is not cited by any requirement. It sits under **Client** Capabilities. `ACP-EXT-202`'s actual basis is `extensibility.mdx:93,126`, which is byte-identical in the draft, and draft `initialization.mdx:115` still says capabilities can be advertised via `_meta`. It has no requirement impact.

The draft tree does add some normative text next to existing coverage: `notice`, `compaction_*`, `plan_removed` and markdown/file plans, the `nes` capability, and `auth_required` on `session/new`. One of these creates a false-FAIL risk for `ACP-RESUME-202` (F3).

## Key findings

- **F1: the `prompt-lifecycle.mdx` line numbers are already stale at the pinned revision.** Every `prompt-lifecycle.mdx:N` citation matches the file at `8f76d6c`. The TCK's `SCHEMA_REVISION`/`VENDORED.md` pin `d8805733`, but commit `0d553a5` (2026-09-23, "list session update variants") inserted 29 lines near the top of the stable file. So at the pin (and at HEAD), stable line = cited + 29 for every cited line ≥12. The draft line numbers in the table below are computed from the *intended* text, not from the stale numbers. No other stable file changed between `8f76d6c` and HEAD, apart from a 1-line type change in the generated `schema.mdx`, so all other stable citations are exact at the pin.
- **F2: several draft files are byte-identical to their stable counterparts:** `transports.mdx`, `extensibility.mdx`, `error.mdx` (all 0 diff lines). Several more differ only in link targets or line wrapping: `session-list`, `session-delete`, `elicitation`, `authentication`, `content`, `slash-commands`. `migration.mdx` exists only in the stable tree: `ls docs/protocol/v2/draft/` has no `migration.mdx`.
- **F3: draft-only normative text touching covered areas** (see the last section).

## Citation table

Line numbers are "cited → draft". The mapping is: stable is from `d8805733` (== HEAD) for every file except `prompt-lifecycle.mdx`, which is from `8f76d6c`; draft is `docs/protocol/v2/draft/<file>` @ `9af0e9f`. "M" means the citation is into `migration.mdx`, which has no draft file.

| Requirement | Current citation | Draft counterpart | Cat. | Note |
|---|---|---|---|---|
| ACP-INIT-001 | initialization.mdx:24,47 | draft/initialization.mdx:24,51 | ii | +4 from the expanded example `capabilities` at draft:37-41 |
| ACP-INIT-201 | initialization.mdx:92-96 | :96-100 | ii | Version-negotiation MUSTs identical |
| ACP-INIT-003 | initialization.mdx:94 | :98 | ii | |
| ACP-INIT-202 | initialization.mdx:94,96 | :98,100 | ii | |
| ACP-INIT-203 | initialization.mdx:248 | :257 | ii | "Both Clients and Agents MUST provide … `info`" identical |
| ACP-INIT-204 | migration.mdx:181 | none (M). Nearest: draft/initialization.mdx:150-156 (session), :160-165 (nes), :166-170 (auth), :216-235 (prompt markers), each "Omitted or `null` … Supplying `{}` means …" | M | No single "every support marker is an object" sentence in the draft tree. The rule survives per field and in `schema.unstable.json`. The draft adds a new `nes` marker (see F3). |
| ACP-SCHEMA-001 | initialization.mdx (whole file) | draft/initialization.mdx | iii | File-level differences: example, `nes`, dropped client `_meta` sentence. None bears on "validates against schema". |
| ACP-SESSION-001 | session-setup.mdx:69 | draft/session-setup.mdx:71 | ii | |
| ACP-SESSION-002 | session-setup.mdx:69,306 | :71,316 | ii | |
| ACP-PROMPT-201 | prompt-lifecycle.mdx:124-127 | draft/prompt-lifecycle.mdx:157-160 | ii | Stale at pin (F1): stable HEAD :153-156 |
| ACP-PROMPT-203 | prompt-lifecycle.mdx:129 | :162 | ii | Stable HEAD :158 |
| ACP-PROMPT-203 | migration.mdx:261 | none (M); same MUST at draft/prompt-lifecycle.mdx:162 | M | Redundant with the line above; drop or repoint |
| ACP-STATE-201 | prompt-lifecycle.mdx:159,348 | :192,462 | ii | Stable HEAD :188,377 |
| ACP-STATE-201 | migration.mdx:278 | none (M); same MUST at draft/prompt-lifecycle.mdx:192 | M | |
| ACP-STATE-202 | prompt-lifecycle.mdx:348 | :462 | ii | |
| ACP-STATE-202 | migration.mdx:282 | none (M); same MUST at draft/prompt-lifecycle.mdx:462 | M | |
| ACP-STATE-203 | prompt-lifecycle.mdx:348,464-481 | :462,578-595 | ii | Stop-reason list plus the "`_` MUST" line identical |
| ACP-STATE-203 | extensibility.mdx:113-118 | draft/extensibility.mdx:113-118 | i | |
| ACP-PROMPTCAP-001/002/003 | initialization.mdx:201-226 | draft/initialization.mdx:210-235 | ii | Only :205's link changed (draft:214) |
| ACP-PROMPT-003 | initialization.mdx:203 | :212 | ii | The baseline text + resource_link MUST is identical, so the conflict with content.mdx survives |
| ACP-PROMPT-003 | content.mdx:33 | draft/content.mdx:33 | i | |
| ACP-PERM-201 | tool-calls.mdx:194,233,253 | draft/tool-calls.mdx:196,235,255 | ii | |
| ACP-CLIENTCAP-201 | elicitation.mdx:54,166 | draft/elicitation.mdx:54,166 | i | |
| ACP-CLIENTCAP-202 | migration.mdx:53-54,628-637 | none (M). The draft tree never mentions `fs/*`/`terminal/*`. | M | The rule survives via `meta.unstable.json` (agent→client inventory; note it **adds `mcp/message`**) |
| ACP-CLIENTCAP-202 | extensibility.mdx:43,52 | same | i | |
| ACP-INFO-CONCURRENT-201 | docs/rfds/v2/prompt.mdx:86 | n/a (RFD, not the doc tree; unchanged since pin) | n/a | Keep |
| ACP-INFO-UNKNOWNSESSION-001 | error.mdx | draft/error.mdx | i | Still a stub, byte-identical |
| ACP-CANCEL-201 | prompt-lifecycle.mdx:519,526 | :633,640 | ii | Stable HEAD :548,555 |
| ACP-CANCEL-201 | migration.mdx:317 | none (M); same MUST at draft/prompt-lifecycle.mdx:633 | M | |
| ACP-CANCEL-201 | schema.mdx:234-240 | draft/schema.mdx:888-894 | ii | Identical SHOULD list |
| ACP-CANCEL-202 | prompt-lifecycle.mdx:530; cf. :497 | :644; :611 | ii | |
| ACP-CANCEL-203 | prompt-lifecycle.mdx:521-528 (:526) | :635-642 (:640) | ii | |
| ACP-CANCEL-204 | prompt-lifecycle.mdx:517 | :631 | ii | |
| ACP-CANCEL-204 | schema.mdx:234-237 | draft/schema.mdx:888-891 | ii | |
| ACP-CANCEL-205 | overview.mdx:185 | draft/overview.mdx:195 | ii | |
| ACP-CANCEL-205 | transports.mdx:66-67 | same | i | |
| ACP-CANCEL-206 | prompt-lifecycle.mdx:503-511 | :617-625 | ii | |
| ACP-CANCEL-207 | prompt-lifecycle.mdx:481 | :595 | ii | |
| ACP-CANCEL-208 | session-setup.mdx:258 | draft/session-setup.mdx:265-267 | ii | Reflowed onto 3 lines, link retargeted; MUST identical |
| ACP-INFO-CANCEL-201 | prompt-lifecycle.mdx:499-536 | :613-650 | ii | |
| ACP-INFO-CANCEL-202 | cancellation.mdx:14,18,60-61 | draft/cancellation.mdx:14,18,60-61 | iii | :14 "remains optional" → "will remain optional"; MAY at :18 identical |
| ACP-TRANSPORT-201 | transports.mdx:23-24,27 | same | i | transports.mdx byte-identical |
| ACP-TRANSPORT-002 | transports.mdx:6 | same | i | |
| ACP-TRANSPORT-203 | transports.mdx:25 | same | i | |
| ACP-JSONRPC-001 | transports.mdx:68-69 | same | i | |
| ACP-JSONRPC-001 | overview.mdx:189 | draft/overview.mdx:199 | ii | |
| ACP-JSONRPC-002 | overview.mdx:183-184 | :193-194 | ii | |
| ACP-JSONRPC-003 | overview.mdx:185; transports.mdx:64-67 | overview :195; transports same | ii / i | |
| ACP-JSONRPC-004 | extensibility.mdx:80-91 | same | i | |
| ACP-JSONRPC-005 | overview.mdx:179-185; extensibility.mdx:80-91 | overview :189-195; ext same | ii / i | |
| ACP-BATCH-201..207 | transports.mdx:57-59 / 66-67,70-72 / 73-75 / 62-65 / 68-69 / 60-61 / 47-51 | same | i | |
| ACP-BATCH-208 | transports.mdx:77-80 | same | i | |
| ACP-BATCH-208 | migration.mdx:722 | none (M); covered by transports.mdx:77-80 | M | Redundant; drop |
| ACP-INFO-BATCH-201 | transports.mdx:55-56 | same | i | |
| ACP-SESSION-203 | migration.mdx:598 | none (M). Draft prose never says "omitted ≡ `[]`". | M | Still grounded in `schema.unstable.json` `NewSessionRequest.required == ["cwd"]` (checked: `mcpServers` optional in both schemas) |
| ACP-RESUME-201 | session-setup.mdx:83-84 | :85-86 | ii | |
| ACP-RESUME-202 | session-setup.mdx:144-145,221-222 | :146-147,227-228 | ii | **The draft adds a `notice` carve-out at :155-158**, see F3 |
| ACP-RESUME-203 | session-setup.mdx:118-119 | :120-121 | ii | |
| ACP-RESUME-204 | session-setup.mdx:199-201; prompt-lifecycle.mdx:153 | :205-207; draft/prompt-lifecycle.mdx:186 | ii | The p-l line is link-only different |
| ACP-RESUME-205 | session-setup.mdx:208-212 | :214-218 | ii | |
| ACP-LIST-201 | session-list.mdx:10,73,108 | draft/session-list.mdx:10,73,108 | i | :10 link target only |
| ACP-LIST-202/203 | session-list.mdx:145 / 63-66 | same | i | |
| ACP-LIST-204 | session-list.mdx:115-117 | same | i | |
| ACP-LIST-204 | overview.mdx:176 | draft/overview.mdx:186 | ii | |
| ACP-CLOSE-201 | session-setup.mdx:237-239,258-268 | :243-245,265-277 | ii | |
| ACP-CLOSE-202 | session-setup.mdx:258; prompt-lifecycle.mdx:519,526 | :265-267; draft/p-l:633,640 | ii | |
| ACP-DELETE-201/202/203 | session-delete.mdx:35,57,74-86 / 90 / 91 | same | i | |
| ACP-ADDDIRS-201 | session-setup.mdx:274-302 | :284-312 | ii | |
| ACP-ADDDIRS-202 | session-setup.mdx:276-277,300 | :286-287,310 | ii | |
| ACP-MCP-201 | session-setup.mdx:336-386,440,465 | :346-396,450,475 | ii | |
| ACP-MCP-202 | session-setup.mdx:388-436 | :398-446 | ii | |
| ACP-CONFIG-201 | session-config-options.mdx:76-129 | draft/…:93-146 | ii | +17 from a new example option (`category: "model_config"`, already in stable schema) |
| ACP-CONFIG-202 | session-config-options.mdx:262,307-312 | :279,324-329 | ii | |
| ACP-CONFIG-203 | session-setup.mdx:232-233 | :238-239 | ii | |
| ACP-CONFIG-204 | session-config-options.mdx:99-108,197 | :116-125,214 | ii | |
| ACP-CONFIG-206 | session-config-options.mdx:314-365 | :331-382 | ii | |
| ACP-AUTH-205 | schema.mdx:428 | draft/schema.mdx:1167 | ii | Identical "May return an `auth_required` error". The draft also adds session-setup.mdx:10, see F3 |
| ACP-AUTH-206 | authentication.mdx:120-122; extensibility.mdx:111-121 | same; same | i | |
| ACP-PATCH-201 | prompt-lifecycle.mdx:246 | :277 | ii | Stable HEAD :275. Draft drops the "#### Message IDs" heading above it; MUST identical |
| ACP-PATCH-203 | prompt-lifecycle.mdx:151 | :184 | ii | |
| ACP-PATCH-205 | agent-plan.mdx:71 | draft/agent-plan.mdx:137 | ii | +66 from the new "Unstable Plan Operations" section; draft :10 also restates "every plan format includes a required `planId`" |
| ACP-PATCH-206 | tool-calls.mdx:405-411,439-440 | :407-413,441-442 | ii | |
| ACP-PATCH-207 | tool-calls.mdx:441-446,466-474 | :443-448,468-476 | ii | |
| ACP-PATCH-208 | tool-calls.mdx:44-52 | draft/tool-calls.mdx:42-55 (title :42-45, name :47-55) | iii | `name` moved below `title`. "The optional programmatic name … SHOULD include it in the first report when available" became "The programmatic name … SHOULD include the name the first time they report a `toolCallId` when it is available". The SHOULD/SHOULD NOT are unchanged, and `name` is still optional in `schema.unstable.json` (`ToolCallUpdate.required == ["toolCallId"]`). |
| ACP-PATCH-209 | prompt-lifecycle.mdx:371 | :485 | ii | Stable HEAD :400 |
| ACP-ENUM-201 | extensibility.mdx:111-118 | same | i | |
| ACP-ENUM-201 | tool-calls.mdx:75,373; agent-plan.mdx:88,100 | tool-calls :77,375; agent-plan :154,166 | ii | |
| ACP-ENUM-202 | extensibility.mdx:117,120 | same | i | New open-enum sites in the draft, see F3 |
| ACP-ENUM-203 | extensibility.mdx:115,122 | same | i | |
| ACP-EXT-001 | extensibility.mdx:43,52,65,109 | same | i | |
| ACP-META-001 | extensibility.mdx:10,33-37,39 | same | i | |
| ACP-EXT-201 | extensibility.mdx:109 | same | i | |
| ACP-EXT-202 | extensibility.mdx:93,126-149 | same | i | Unaffected by the initialization.mdx:116-117 drop (that sentence is client-side and uncited) |
| ACP-ERROR-001 | overview.mdx:181-185 | draft/overview.mdx:191-195 | ii | |
| ACP-SHUTDOWN-001 | transports.mdx:41 | same | i | |
| ACP-SCHEMA-002 | extensibility.mdx:39,113-120 | same | i | |
| ACP-STDERR-001 | transports.mdx | draft/transports.mdx | i | |
| ACP-INFO-PARSE-001 / INVALIDREQ-001 | error.mdx | draft/error.mdx | i | |

These requirements have no prose citation (schema/meta only), so they are out of scope here: PROMPT-205, AUTH-201, AUTH-202, AUTH-203, AUTH-204, AUTH-207, PATCH-204, META-201, EXT-203, INFO-BATCH-202.

**Docstring-only citations** (`src/tck/v2/conformance/*`, `tests/fixtures/agents/v2/*`): these mirror the rows above and map the same way. The one extra is `tool-calls.mdx:304` (`_helpers.py:770`, `test_cancel.py:457`), which becomes draft `:306` (ii, link-only). The prompt-lifecycle numbers in `test_patches.py:76,92,273`, `test_cancel.py:9`, and `_helpers.py:739,784` carry the same F1 staleness. `migration.mdx:181` in `test_initialize.py:196` and `boolean_session_capability.py:4` is M.

**Counts** (one per requirement × cited-file pair, 116 pairs): (i) 43, (ii) 61, (iii) 3, (iv) 0, M (migration-only) 8, n/a (RFD) 1.

## Draft-only normative text touching covered areas (F3)

| Draft location | Statement | Touches |
|---|---|---|
| draft/prompt-lifecycle.mdx:352-396; draft/session-setup.mdx:155-158 | `notice` update: Agent **MAY** send one "at any point while a session exists, including outside prompt processing". Notices **SHOULD NOT** be replayed. "If the underlying condition is still relevant after resuming finishes, the Agent may emit a new notice." | **ACP-RESUME-202**: `test_resume_with_replay_from_start_replays_before_responding` FAILs on *any* same-session `session/update` in the post-response quiet period, so a live notice emitted right after resume would false-FAIL. (This is already latent for `available_commands_update`/`usage_update`/`session_info_update`; the draft now blesses it explicitly.) ACP-RESUME-203 is safe because it filters to history/chunk kinds. |
| draft/prompt-lifecycle.mdx:373-377 | `notice.severity` is an open string enum: values starting with `_` are reserved for extensions, and other unknown values are reserved for future ACP. No MUST. | ACP-ENUM-202 (new open-enum site), ACP-SCHEMA-002 `other`-branch carve-out |
| draft/prompt-lifecycle.mdx:400-430 | `compaction_update` / `compaction_summary_chunk`: MAY. Chunks are sent "only between an `in_progress` update and its terminal update". Unknown `status` strings are preserved by receivers (no `_` rule stated). | ACP-ENUM-202 (`sessionUpdate` discriminator gains 3 known values plus `plan_removed`); ACP-RESUME-205-style ordering is not covered |
| draft/agent-plan.mdx:10, :67-132 (:71, :113) | Markdown/file plan types and `plan_removed`. "Plan file URIs **MUST** be absolute." Clients **MUST** tolerate the variants (client-side). | ACP-PATCH-205 (planId on all formats, still consistent); absolute-path theme of ACP-LIST-204/PATCH-206 (a new agent-side MUST not currently asserted) |
| draft/initialization.mdx:160-165 | New `capabilities.nes` object marker (the unstable schema also adds `providers` and `positionEncoding` to `AgentCapabilities`) | ACP-INIT-204's enumerated "known markers (`session`, `auth`, …)"; ACP-EXT-202/SCHEMA-002 root-key checks |
| draft/session-setup.mdx:10 | "`session/new` may fail with an `auth_required` error until the Client completes the authentication flow" (lowercase may) | ACP-AUTH-205. Consistent with its ADVISORY tier; the draft simply adds a second citation. |
| draft/schema.mdx (generated from `schema.unstable.json`) | Unstable-RFD surfaces with "must" text: `nes/close` (:499), `providers/*`, `mcp/message`, `session/fork` | Outside current coverage; `mcp/message` enters the ACP-CLIENTCAP-202 agent→client inventory via `meta.unstable.json` |

## Discrepancies

- The pinned revision vs. the `prompt-lifecycle.mdx` citations (F1): stale by +29 lines at `d8805733`.
- `schema.json`/`schema.unstable.json` `AgentCapabilities.session` description lists a 4-method baseline, while draft/stable `initialization.mdx:150-156` lists 7. This predates the switch, is identical in both schemas, and is noted only for completeness.

## Open questions

- `positionEncoding` in the unstable `AgentCapabilities` is a `PositionEncodingKind` (not an object marker). Would ACP-INIT-204's check need to exempt it if its implementation walks every key? This is schema-side, so route it to whoever owns the schema switch.
- Should ACP-RESUME-202's trailing-update drain exclude non-history kinds (`notice`, plus the pre-existing background kinds)? That is a requirement/test design decision.
