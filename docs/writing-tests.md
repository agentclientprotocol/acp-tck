# Writing requirements and tests

How to add a requirement and its conformance test. The id, tier and citation rules are in
[requirements.md](requirements.md); the prompt driver is in [mock-client.md](mock-client.md). The steps below are
the same for v1 and v2; substitute the version package (`src/tck/v1/` or `src/tck/v2/`).

## Adding a requirement and a test

1. Add a `Requirement(...)` to `_DECLARATIONS` in `src/tck/v{1,2}/requirements.py`: an id
   (`ACP-<AREA>-<NNN>`, see [Ids](requirements.md#ids)), a `Tier`, the capability gate if the tier is
   `CAPABILITY`, one-sentence `text`, and the upstream `citation` ([Citations](requirements.md#citations)). Take the
   rule from the spec text, not from memory of the protocol.
2. Write the test under `src/tck/v{1,2}/conformance/`, marked `@pytest.mark.requirement("ACP-...")`, with a
   docstring that starts with the id(s). Use `connected_agent()` from `_helpers.py` to spawn the agent; `async def`
   tests work without extra setup.
3. If the row applies only when the agent advertises a capability in `initialize`, add `@pytest.mark.capability(path)`
   (below). If the feature has no `initialize` marker, use an [`inferred:` gate](requirements.md#inferredfeature-gates)
   instead: no marker, and the test skips itself.
4. If the test sends a probe the agent is not expected to recognize, follow the [probe rules](#probes).
5. Run `uv run pytest`. The registry tests (`tests/v{1,2}/test_registry.py`) fail if the id is not referenced by a
   test, if a test references an unregistered id, and, because they pin the id set and the per-tier id sets by
   hand, if you did not update those. `tests/v{1,2}/test_cli.py` keeps hand-written tier sets that must match the
   registry too.
6. Add a non-conforming fixture that trips only the new row, and assert it in `tests/v{1,2}/test_cli.py`
   ([Fixtures](#fixtures)).

## Markers

### `capability`

`@pytest.mark.capability("agentCapabilities.some.path")` makes the test SKIP with a "capability not advertised"
reason unless the path is advertised in the `initialize` result. The path is dotted from the result root, and the
row's `capability` field names the same path.

- By default the path is an *object marker*: advertised if the value is present and neither `null` nor `false`
  (so `{}` counts).
- `boolean=True` is for a plain boolean flag: advertised only if the value is exactly `true`.

See `capability_is_supported()` in `src/tck/common/plugin.py`. If `initialize` itself failed, a capability-gated
test FAILs rather than SKIPs, so a broken agent cannot score well by never advertising anything.

**Never pass an `inferred:<feature>` path to the marker.** That string is documentation only
([`inferred:` gates](requirements.md#inferredfeature-gates)); the marker would SKIP on every agent and the run would
false-PASS. `pytest.skip` inside the test instead, when the agent shows no use of the feature.
`tests/common/test_capability_markers.py` fails if a conformance test does it.

### `revokes`

`@pytest.mark.revokes("auth", reason=...)` marks a test that takes away something other tests rely on (today only
the logout tests). The common plugin moves it to the end of the run, keeping collection order otherwise. At most
one `revokes` test may be collected per run (`pytest.UsageError` otherwise; a second would need dependency
ordering). Do not use it for archiving or deleting the TCK's own sessions.

## Probes

A probe is traffic the TCK sends that a conforming client would not.

- A custom method, notification or value must be `_`-prefixed (`_tck/does_not_exist`, `_tck_unadvertised_method`,
  `_tck_unknown`). The extensibility rule requires custom names to start with `_`, and the TCK holds its own probe
  traffic to it, so a probe cannot collide with anything the agent knows.
- A probe may break a rule that binds the client (send a relative `cwd`, an unadvertised `methodId`, an invalid
  block) **only where the spec defines the agent's answer to exactly that input**. Say so in the row text and the
  test docstring: which client rule is broken, why, and what the spec says the agent does.

## Error-code policy

Spec sentences that say an agent rejects something often do not carry an RFC keyword on the code, or do not name
it at all. Split the row accordingly:

- A `MANDATORY` or `CAPABILITY` row asserts **error versus success**: the request is rejected with a JSON-RPC
  error and not answered with a result (and, where it matters, nothing was inserted, loaded or created).
- The **exact code** is asserted in that row only where a MUST names it.
- A declarative or SHOULD-level code goes in a **separate `ADVISORY` row** with its own id. It SKIPs when nothing
  was rejected, since that is the other row's concern.

Examples, all in v2: `ACP-AUTH-208` (rejected) and `ACP-AUTH-210` (`-32602`); `ACP-SESSION-204` and
`ACP-SESSION-209`; `ACP-LIST-205` and `ACP-LIST-207`.

## SKIP or FAIL

A SKIP says "nothing was judged", so it must be honest.

- **SKIP** when a precondition legitimately does not hold, with a reason that says which: the capability is not
  advertised, the agent has no session to restore, the probe needs an advertised `authMethods` and there are none.
- **FAIL** when an agent defect breaks the test's own setup. If the agent cannot complete `initialize`, create a
  session or finish a turn, the rows that depend on it fail, they do not skip. An uncaught `AgentTimeout` or
  `AgentExited` is a FAIL.
- **Unavoidable races** SKIP rather than guess. A cancellation that could not land (the turn ended before
  `session/cancel` was sent, or a plausible self-reached stop reason arrived within the race window) SKIPs with
  "cancellation not exercised"; see [mock-client.md](mock-client.md#cancel-races). `--cancel-prompt` makes this
  less likely against a real agent.
- **`AUTH-GATED:`** in a SKIP message marks a test the agent's authentication requirement kept from running
  (`skip_if_auth_gated`, and `skip_if_login_times_out` for a login that never answers). It sets
  `blocked_by_auth`, which forces the run NOT CONFORMANT. A failed login inside an authentication row does not
  carry the marker and does not block the verdict.
- **`VERSION-MISMATCH:`** marks a test whose judgement depends on the agent speaking the targeted protocol version
  when it negotiated a different one (or rejected `initialize` with `-32022`). It sets
  `blocked_by_version_mismatch`, also forcing NOT CONFORMANT. Rows that judge only the negotiation outcome are
  judged normally and do not skip. Tests marked `@pytest.mark.negotiation` still run when `initialize` was
  rejected with `-32022`. Only v2's version-tolerant `ACP-INIT-*` rows carry it. v1 marks none: its negotiation
  rule ("respond with the latest version it supports") predates `-32022` and cannot judge a v2-only agent.

## Fixtures

`tests/fixtures/agents/v{1,2}/` holds fixture agents that the CLI tests run the TCK against.

- Pure stdlib, deterministic, offline. A fixture is launched as a standalone subprocess and shares code with its
  siblings through its directory's `_base.py`.
- `conforming.py` is the baseline. Every other fixture has **one defect** and trips exactly the row(s) named in its
  filename and docstring.
- The docstring lists the rows the fixture FAILs and any intended cascade (rows that fail as a consequence, and
  rows that deliberately do not).
- `tests/v{1,2}/test_cli.py` asserts each fixture's **exact FAIL set**, so a change that moves a row for the wrong
  fixture is caught.
- Some tests scope the run with `-k` to the module(s) that own the ids they assert on. That flips the printed
  verdict to NOT CONFORMANT (every unselected MANDATORY row is NOT_TESTED). When a run is scoped, the fixture's
  docstring says its FAIL set holds "within its `-k` scope".
- Cover both sides: `conforming.py` (or a fixture that advertises the capability) PASSes the row, and the defect
  fixture FAILs it.
