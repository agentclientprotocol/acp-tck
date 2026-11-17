# Impact research (v1): tool-calls.mdx, terminals.mdx, file-system.mdx, spec 3961af94 -> 3ea94133

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (checkout
`/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`), diffed against `3961af94`:
`docs/protocol/v1/draft/{tool-calls,terminals,file-system}.mdx` (all read in full at the target),
`docs/protocol/v1/draft/initialization.mdx` (client-capabilities diff), `docs/protocol/v1/draft/subagents.mdx:310-330`,
`docs/rfds/subagents.mdx:640-665` (stage **Preview** at the target, from `docs/docs.json`; it was Active),
`schema/v1/schema.unstable.json#/$defs/ToolCallUpdate`, `#/$defs/SessionReference`. acp-tck: `src/tck/v1/requirements.py`,
`spec-tracker/maps/v1.toml`, `src/tck/v1/conformance/_helpers.py:798-840`. I did not consult the SDKs because no
rule needed runtime behaviour the spec leaves implicit.
**Confidence:** high. The only prose change is one hunk in tool-calls.mdx. `terminals.mdx` and `file-system.mdx`
are byte-identical between the two revisions (`git diff --quiet` succeeds), and the initialization.mdx
client-capabilities hunks add only prompt suggestions, cursors and subagents, so nothing touches `fs` or `terminal`.

## What changed in tool-calls.mdx

- Line 340: the subagent link now points to `/protocol/v1/draft/subagents` instead of `/rfds/subagents`.
- Line 358: "The task a parent sends a child" now reads "A message a parent sends a child". The clause the TCK cites,
  "Agents send it only when the Client advertises the `subagents` capability", is unchanged and still on line 358.
- Lines 361-365 are new, which shifts every later line by +5:
  > `content` on `tool_call_update` replaces the whole array, so an Agent that sends new content includes the
  > session references again. When a tool addresses a session by a name or another handle, the Agent adds a
  > reference only if it can resolve the handle to a known session.

  Neither sentence uses an RFC 2119 keyword. The Preview RFD says the same thing at `docs/rfds/subagents.mdx:655-661`
  and adds two things: "or the update removes them", and "It **MUST NOT** guess the session."

## tool-calls.mdx

| id / ledger citation | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-CLIENTCAP-007 (`tool-calls.mdx:358`) | citation-only (RFD part) | `tool-calls.mdx:358` (same line); `docs/rfds/subagents.mdx:76-78,663-664 (Preview RFD)` | The cited clause is unchanged. The RFD lines 644-645 moved to 663-664, and the label changes from Active to Preview. The row's other citations (prompt-turn) belong to another researcher. |
| ACP-SUBAGENT-002 (`tool-calls.mdx:349-351`) | citation-only (RFD part) | `tool-calls.mdx:349-351`; `docs/rfds/subagents.mdx:647-650 (Preview RFD)` | The rule is unchanged. You may also cite `tool-calls.mdx:364-365` as support, because the handle sentence reduces to the same observable rule (the referenced session must be known). The test needs no change: re-sent references in a replacing `tool_call_update` are judged again against `known`, which is correct. |
| ACP-PERM-001 (`tool-calls.mdx:247`) | unchanged | `tool-calls.mdx:247` | |
| ACP-PERM-002 (`tool-calls.mdx:249`) | unchanged | `tool-calls.mdx:249` | |
| ledger `tool-calls.mdx:247` | unchanged | `:247` | |
| ledger `tool-calls.mdx:250` | unchanged (reason flagged) | `:250` | See Decision 3. |
| ledger `tool-calls.mdx:238-242,251` | unchanged | `:238-242,251` | |
| ledger `tool-calls.mdx:252` | unchanged | `:252` | |
| ledger `tool-calls.mdx:377-381; overview.mdx:231; …/ToolCallLocation/properties/line` | citation-only | `tool-calls.mdx:382-386` | The text is unchanged and shifted by +5. The `overview.mdx:231` part belongs to the overview researcher, because overview.mdx gained 3 lines before 225 and the line probably moved. |

## terminals.mdx

| id / ledger citation | classification | target citation | note |
|---|---|---|---|
| ACP-CLIENTCAP-002 (`terminals.mdx:10,26`) | unchanged | `terminals.mdx:10,26` | The doc is identical at both revisions. |

No ledger entries cite terminals.mdx.

## file-system.mdx

| id / ledger citation | classification | target citation | note |
|---|---|---|---|
| ACP-CLIENTCAP-001 (`file-system.mdx:10,29`; `FileSystemCapabilities`) | unchanged | `file-system.mdx:10,29` | The doc is identical at both revisions. |

No ledger entries cite file-system.mdx.

## New requirements

None. Neither new sentence carries a keyword, and both are covered as follows:

- The handle sentence (`:363-365`) has one observable consequence: a reference that names an unknown session.
  ACP-SUBAGENT-002 already judges exactly that.
- The replace sentence (`:362-363`) describes the consequence of replace semantics. The Preview RFD
  (`subagents.mdx:656`) says that an update that leaves the references out removes them, so leaving them out is
  not a violation.

## New ledger entries

These are proposed for the `# --- tool-calls.mdx ---` block of `spec-tracker/maps/v1.toml`.

1. `citation = "docs/protocol/v1/draft/tool-calls.mdx:362-363; docs/rfds/subagents.mdx:655-657 (Preview RFD)"`
   - statement: "`content` on `tool_call_update` replaces the whole array, so an Agent that sends new content
     includes the tool call's session references again."
   - reason: "Not a constraint the TCK can judge. The statement carries no RFC 2119 keyword, and the Preview RFD
     says an update that leaves the references out removes them. A client cannot tell an intended removal from a
     forgotten re-send, because the agent's intended display state is not on the wire."

2. `citation = "docs/protocol/v1/draft/tool-calls.mdx:363-365; docs/rfds/subagents.mdx:659-661 (Preview RFD)"`
   - statement: "When a tool addresses a session by a name or another handle, the Agent adds a `session` reference
     only if it can resolve the handle to a known session, and does not guess the session (MUST NOT, Preview RFD)."
   - reason: "Not observable beyond ACP-SUBAGENT-002. A reference to an unknown session FAILs that row, but a guess
     that lands on a known yet wrong session looks the same on the wire as a correct resolution, because the
     handle-to-session mapping is internal to the agent."

Both reasons rest on what can be seen on the wire, not on any TCK choice.

## Decisions for the user

1. **Whether to record the two new sentences in the ledger.** I recommend adding ledger entries 1 and 2 and no new
   row. The RFD's "MUST NOT guess" is an RFD-only MUST, so it would be capped at CAPABILITY in any case. It cannot be
   decided from the client side, so the ledger is the right place for it.
2. **Whether to add `tool-calls.mdx:364-365` to ACP-SUBAGENT-002's citation.** This is optional. I lean towards yes,
   because it is the docs' newest statement of the known-session rule for references.
3. **Existing ledger reason at `tool-calls.mdx:250`, which is borderline TCK-choice.** The reason says "the operation
   is not on the wire in v1". That is true only because the mock client advertises no `fs`/`terminal`. With those
   capabilities, a write or command would appear as `fs/write_text_file` or `terminal/create`. Even then, the
   "described" operation is free text (`title`, `rawInput`), so the rule remains undecidable. I recommend rewording
   the reason to: "Not decidable: the approved request describes the operation only in agent-authored, free-form
   fields (`title`, `rawInput`, content), so the TCK cannot tell whether a later operation or changed target matches
   it." That removes the dependence on the mock client.
4. **Pre-existing gaps in unchanged text (outside this diff; follow-up only, so route as you see fit).** v1 has no
   row and no ledger entry for these agent-side rules:
   - `terminals.mdx:109-110` and `:249`: the Agent MUST release terminals with `terminal/release`. This becomes
     observable once the mock client advertises `terminal: true` and implements `terminal/*`. It would be a
     CAPABILITY row gated on `clientCapabilities.terminal`, or a "Deferred" ledger entry naming the missing mock
     terminal support.
   - `tool-calls.mdx:14`: the Agent SHOULD report tool calls.
   - `tool-calls.mdx:48-49`: the Agent SHOULD include `name`, and SHOULD NOT change it except to correct metadata.
     This is observable as ADVISORY across `tool_call` and `tool_call_update`.
5. **Stale label in code, not in the registry.** The `session_content_references` docstring
   (`src/tck/v1/conformance/_helpers.py:808-810`) says "Active Subagents RFD". It should say Preview, or cite
   `tool-calls.mdx` instead. Pick this up with the RFD label refresh.
