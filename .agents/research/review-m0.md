# Review: M0 (RFD policy), 6faf774..dbaafc1

Scope: commit dbaafc1. It changes `.agents/skills/update-to-spec/SKILL.md`, `docs/requirements.md`,
`docs/spec-updates.md`, and relabels the subagents citations in `src/tck/v2/requirements.py` and
`src/tck/v2/conformance/test_session_capabilities.py`.

Verified:
- The relabels are correct. At pin 3961af94, `docs/docs.json` puts `rfds/subagents` in the top-level
  `Active` group. All five edited strings now read `(Active RFD)` / `Active Subagents RFD`, and the
  cited line ranges still say what the rows claim.
- `tests/v{1,2}/test_registry.py` passes on a clean `git archive dbaafc1` export (33 passed). The
  live working tree has uncommitted S2.1 work that makes 2 v2 registry tests fail. That work is not
  part of this range.
- The `inferred:` description matches the code. `_tck_capability_gate` only reads a
  `@pytest.mark.capability` marker. No `inferred:` row carries one. v1 `test_session_config.py` and
  v2 `ACP-CONFIG-201` and the rows after it self-skip when the field is missing.
- The tier cap holds for the existing MANDATORY rows that cite RFDs, because the docs state both
  rules too:
  - v1 `ACP-CLIENTCAP-007`: `prompt-turn.mdx:19-21` says "Requires the Client's `subagents`
    capability" for all three update kinds, and `tool-calls.mdx:358` says "Agents send it only when
    the Client advertises the `subagents` capability".
  - v1 `ACP-PLAN-001`: `agent-plan.mdx:127` says "Plan file URIs **MUST** be absolute".
- In both modes, step 4 now reaches a tracked RFD whose content changed, so the subagents miss
  (Draft to Active, +513 lines in beac4ba9..3961af94) would be caught.

## Findings

1. **should-fix**: `.agents/skills/update-to-spec/SKILL.md:37-39`, `docs/spec-updates.md:40-42`
   - **Defect:** "plus any RFD that moved into Active or later within the range" contradicts "Skip
     Completed RFDs". Completed is "later" in the Draft → Active → Preview → Completed lifecycle. And
     an RFD that is Active or Preview at the target is already covered by the first clause. So the
     "plus" clause either adds nothing or adds exactly the Completed RFDs that the next sentence
     excludes.
   - **Scenario:** In the last range (beac4ba9..3961af94), `rfds/client-system-prompt` went from
     Draft to Completed and changed by 35 lines. One researcher tracks it under the "plus" clause,
     another skips it as Completed. Its rules may have landed in the docs, so a skip can leave
     re-tiering undone.
   - **Confidence:** confirmed by reading (`docs.json` at both pins).

2. **should-fix**: `.agents/skills/update-to-spec/SKILL.md:34,61-62`, `docs/requirements.md:118-122`
   - **Defect:** Nothing reliably detects a stage move, and nothing keeps stage labels current:
     - The inventory asks only for each RFD's stage *at the target*, not at the base.
     - `spec-impact` never reads `docs/docs.json`. Its scope is the draft tree, `schema/v<N>` and
       `docs/rfds/` (`spec-tracker/src/spec_tracker/impact.py:69`). `docs/docs.json` is diffed only
       in the by-hand fallback.
     - The re-vendor slice remaps line numbers only.
   - **Scenario:**
     - An RFD moves stage by a `docs.json`-only edit, for example Draft to Active with no change to
       the `.mdx`. Nobody sees the move, so it gets no researcher. That is the subagents miss
       without the content change.
     - A cited RFD moves Active to Draft or Active to Completed. Rows keep the stale `(Active RFD)`
       label after the pin moves. An RFD that went Completed may also deserve a MANDATORY re-tier
       that nobody proposes.
   - **Confidence:** confirmed by reading.

3. **should-fix**: `.agents/skills/update-to-spec/SKILL.md:38`, `docs/spec-updates.md:40-41`,
   `docs/requirements.md:120`
   - **Defect:** The stage is defined as "its sidebar group in `docs/docs.json`", but the Active
     RFDs for v2 sit in a nested `Active › v2` group. Their innermost group is `v2`, which is not a
     stage, so the rule is ambiguous for them.
   - **Scenario:** This already happened. The S0.1 record in `state.md` says "At pin 3961af94
     Active = subagents, streamable-http-websocket-transport, mcp-over-acp". It misses all 13
     `rfds/v2/*` Active RFDs, including `rfds/v2/background-work` (+391 lines, new in the last
     range). An inventory researcher who reads it the same way drops every v2 RFD.
   - **Fix direction:** say "top-level group; nested groups inherit it".
   - **Confidence:** confirmed by reading.

4. **should-fix**: `.agents/agents/researcher.md:29` (not in the diff)
   - **Defect:** The researcher definition still says "Use RFDs for design intent, and label them
     as proposals, not requirements". That contradicts the new policy, under which Active and
     Preview RFDs carry nearly the weight of a doc and RFD-only MUSTs become CAPABILITY rows. The
     step-4 RFD researchers run under this definition, and per granular-work the agent definition
     wins over the brief.
   - **Scenario:** The dedicated subagents researcher reports "no new requirements: design intent
     only" for its MUSTs. The process is exactly the one meant to stop the miss, yet it misses
     again.
   - **Confidence:** plausible.

5. **should-fix**: `src/tck/v1/requirements.py:1122` (`ACP-CLIENTCAP-007`)
   - **Defect:** This subagents RFD citation has no stage label in its citation or its text. The
     milestone was asked to relabel the subagents citations, and the new rule at
     `docs/requirements.md:119-121` requires a label on every RFD citation. The same gap appears in:
     - `spec-tracker/maps/v1.toml:299` (ledger citation of `subagents.mdx:636-638`);
     - `src/tck/v2/conformance/test_session_capabilities.py:195,285` ("(RFD: subagents)").
   - **Pre-existing unlabeled RFD citations that now violate the written rule:**
     - v1 `requirements.py:996,1013` (get-auth-state, Draft) and `:1141` (`ACP-PLAN-001`,
       plan-operations, Draft);
     - v2 `requirements.py:558,778` (`rfds/v2/prompt`, Active), `:1945` (session-fork, Draft),
       `:2192,2239` (session-config-options, Completed), `:2524` (get-auth-state, Draft).
   - **Scenario:** A report reader cannot tell these citations from the docs' own. The next spec
     update's researchers have no stage to compare against.
   - **Confidence:** confirmed by reading.

6. **should-fix**: `docs/requirements.md:47`, `docs/writing-tests.md:16,29-31`
   - **Defect:** The tier table still defines CAPABILITY as "Applies only when the agent advertises
     the capability in `initialize`; the row names the path" and "SKIPPED (not advertised)". That
     contradicts the new `inferred:` section on the same page. `writing-tests.md` step 3 and its
     `capability` section, which is where a contributor adds a row, never link to the new section.
   - **Scenario:** An M2/M3 programmer follows `writing-tests.md`, sees that "the row's `capability`
     field names the same path", and adds `@pytest.mark.capability("inferred:subagents")`.
     `capability_is_supported(..., "inferred:subagents")` returns `False` (confirmed by running), so
     the test always SKIPs. A CAPABILITY SKIP never affects the verdict, so the run false-PASSes.
     The required non-conforming fixture would catch this, at the cost of a fix cycle.
   - **Confidence:** confirmed by running.

7. **should-fix (process gap)**: `.agents/skills/update-to-spec/SKILL.md:61-62`
   - **Defect:** There is no backfill. Diff mode routes a tracked RFD only when it changes in the
     *next* range. Several RFDs changed in the last range without an RFD researcher:
     - `mcp-over-acp` (Draft to Active);
     - `rfds/v2/background-work` (+391 lines, new);
     - the other Active `rfds/v2/*`.
     Only subagents is being backfilled, by M1-M4.
   - **Scenario:** The next diff-mode update skips these unless they change again, so any RFD-only
     rule they added stays untested and unrecorded.
   - **Fix direction:** one full audit of tracked RFDs, or "a tracked RFD never audited under this
     policy is affected".
   - **Confidence:** plausible. I did not check whether the docs already restate their rules.

8. **nit**: `docs/spec-updates.md:20,45`
   - **Defect:** These lines say tracked RFDs are affected docs "when they changed". The skill says
     "changed (or moved stage)".
   - **Scenario:** Someone following the contract page skips an RFD that only moved stage.
   - **Confidence:** confirmed by reading.

9. **nit**: `docs/requirements.md:56`
   - **Defect:** The example cites `docs/protocol/v1/draft/prompt-turn.mdx:19-21` without a pin.
     `spec-impact --fix` rewrites only `requirements.py` and the maps.
   - **Scenario:** After the next re-vendor the example points at the wrong lines.
   - **Confidence:** confirmed by reading.

10. **nit**: `docs/requirements.md:53-54,118-119`
    - **Defect:** The text leaves two cases open:
      - an RFD-only MUST that binds every agent, with no feature to opt into, fits neither a real
        nor an `inferred:` gate;
      - Completed RFDs are not covered by the citation rule, although v2 cites one
        (session-config-options).
    - **Scenario:** A researcher stalls or picks a tier ad hoc.
    - **Confidence:** plausible.

## Follow-ups (owned elsewhere)

- Ledger reasons that now break the new rule: `spec-tracker/maps/v1.toml:200,205,301` ("the TCK
  never advertises" `subagents`). They are already scheduled for S3.1. `v2.toml:349` uses the same
  phrasing, but only in a section comment, and its entries are marked "Deferred".
