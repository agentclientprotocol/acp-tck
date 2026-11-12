# acp-tck

![Status: experimental](https://img.shields.io/badge/status-experimental-orange)
[![Latest release](https://img.shields.io/github/v/tag/agentclientprotocol/acp-tck?sort=semver&label=release+tag)](https://github.com/agentclientprotocol/acp-tck/tags)

A Test Compatibility Kit for the [Agent Client Protocol](https://agentclientprotocol.com) (ACP). It launches an agent
implementation as a stdio subprocess, drives it through the protocol - initialize, session lifecycle, prompt turns,
cancellation, error handling, transport hygiene - and reports which requirements pass, fail, don't apply, or were never
exercised.

Targets **v1** by default, with an opt-in **v2** suite via `--protocol-version 2`.
Both **v1** and **v2** target unstable spec versions (v1-unstable is a superset of v1-stable, so any v1-stable compatible agent will be judged CONFORMANT).

See ["What is covered"](#what-is-covered) below for the exact per-version breakdown.

> [!NOTE]
> This project is in an experimental state. It does not provide 100% coverage. Requirements, CLI options, the JSON
> report format, and verdicts may change without notice, and a result from this TCK is not an official statement of ACP conformance.
> The v2 suite tracks a draft version of the protocol and is especially likely to change.

## Install and run

Needs [uv](https://docs.astral.sh/uv/); it fetches Python 3.14 if you don't have it. Run the TCK straight from GitHub,
with no checkout:

```bash
uvx --from git+https://github.com/agentclientprotocol/acp-tck@<release tag> acp-tck [args] -- <agent command> [agent args...]
```

Replace `<release tag>` with a tag from [the tags page](https://github.com/agentclientprotocol/acp-tck/tags) (the
latest is on the badge above), or a commit SHA, so results are reproducible. Without `@...`, uv runs the latest
`main`, and may keep reusing a cached copy of it until you pass `--refresh`.

To keep `acp-tck` on your PATH instead:

```bash
uv tool install git+https://github.com/agentclientprotocol/acp-tck@<release tag>
acp-tck [args] -- <agent command> [agent args...]
```

Everything after `--` is the agent's own command line, launched as a stdio subprocess - a fresh process per test, so one
crash can't cascade into unrelated failures. To run the TCK from a checkout instead, see
[`docs/development.md`](docs/development.md#running-the-tck-from-source).

### Examples

Run the v1 suite against an agent from inside its own project directory, using defaults for everything else:

```bash
uvx --from git+https://github.com/agentclientprotocol/acp-tck@<release tag> acp-tck -- node ./dist/index.js
```

Run the v2 suite with a scratch working directory for the agent, longer per-response and per-test timeouts (real
agents are slower than the TCK's own fixtures), and the full JSON report written for later inspection:

```bash
uvx --from git+https://github.com/agentclientprotocol/acp-tck@<release tag> acp-tck \
  --protocol-version 2 \
  --agent-cwd /tmp/acp-tck-wd \
  --timeout 90 --test-timeout 300 \
  --report-json report.json \
  -- node /path/to/some-agent/dist/index.js
```

## Options

### `--protocol-version {1,2}`

Selects which protocol version's conformance suite to run (default `1`); see ["What is covered"](#what-is-covered) for
what each suite checks. If the agent under test never actually negotiates the requested version, version-dependent tests
are `SKIPPED` with a `VERSION-MISMATCH` hint and the run is forced `NOT CONFORMANT` - symmetrically for both directions
(a v1-only agent run under `--protocol-version 2`, or a v2-only agent run under `--protocol-version 1`).

### `--agent-cwd DIR`

Working directory for the agent process (default: inherit from the `acp-tck` process itself). Useful when the agent
expects to be launched from within a particular project or workspace directory.

### `--agent-env KEY=VAL`

An environment variable overlaid on the agent's process environment. Repeatable - pass the flag once per variable to set
several.

### `--timeout S`

Per-response deadline in seconds (default `30`). Bounds how long the harness waits for any single response from the
agent before treating it as unresponsive.

### `--startup-timeout S`

Deadline in seconds for the agent's very first response (default `30`), kept separate from `--timeout` so a
slow-starting agent (e.g. one doing heavyweight initialization work) doesn't force every later response deadline to be
raised too.

### `--test-timeout S`

Wall-clock deadline in seconds for a single test, regardless of its own internal timeouts (default `120`). Guards
against a test that would otherwise hang indefinitely - e.g. an agent that stops responding partway through a multi-step
exchange. On expiry the test fails with a message identifying the watchdog, and the agent process is still shut down
normally.

### `--cancel-prompt TEXT`

Prompt text the cancellation tests send, replacing the default (a request for a long, detailed explanation). Pick
something that keeps a real agent busy long enough for `session/cancel` to land while the turn is still in flight -
otherwise those tests report `SKIPPED` ("cancellation not exercised"), which means exactly that, not a conformance
failure.

Protocol version 2 also uses it for the `tool_call/cancel` and `terminal/cancel` tests (`ACP-TOOLCANCEL-*`,
`ACP-TERMCANCEL-*`), which judge only an agent that advertises `capabilities.cancel` on a tool call or terminal that is
still running. The TCK sends this prompt, watches for such an item (for up to `--timeout` seconds, or until the turn
ends), cancels the first tool call and the first terminal it finds, then sends `session/cancel` for the turn. With the
default essay prompt an agent essentially never has such an item, so those tests report `SKIPPED` ("no tool call
advertised `capabilities.cancel` while still live"). To exercise them, choose a prompt that makes the agent start a
long-running cancellable command or background task.

### `--auth-method ID`

Authenticates with this method id (one advertised in `initialize`'s `authMethods`) right after `initialize`, before any
session-dependent test runs. Needed for any agent that gates `session/new` behind authentication - without it,
session-dependent tests report `SKIPPED` with an "AUTH-GATED" hint and the run is forced `NOT CONFORMANT`, since those
requirements were never actually exercised.

If the login never answers within the timeout (an interactive login may stay pending), the tests SKIP with
`AUTH-GATED:` and a hint instead of failing, and the run is blocked the same way. Use a non-interactive method or raise
the timeouts.

### `--allow-logout`

Opts in to actually calling logout against the agent under test (`ACP-AUTH-004`): `logout` on v1 and `auth/logout`
on v2. Off by default because it may revoke the operator's own credentials for whatever account the agent is
authenticated as; without it, the logout requirement reports `SKIPPED` instead of exercising the method. With it,
the logout test runs last, after every other test. A
`SKIPPED` `CAPABILITY`-tier requirement doesn't affect conformance - only a *failed* one does - so omitting
`--allow-logout` never by itself makes a run `NOT CONFORMANT`.

### `--close-grace S`

Grace period in seconds budgeted at each stage of the shutdown ladder (close stdin, then `SIGTERM`, then `SIGKILL`) when
tearing down the agent process after a test (default `2.0`). Each stage stops early as soon as the agent actually exits,
rather than always waiting out the full grace period, so raising this only matters for a slow-to-exit agent.

### `--report-json PATH`

Writes the full JSON report to `PATH` - see ["Reading the report"](#reading-the-report) below for its shape.

### `-k EXPR`

Runs only tests matching a pytest `-k` expression.

### `-v`

Verbose pytest output.

### `--version`, `--help`

Print the installed `acp-tck` version, or usage help, and exit.

## Reading the report

The terminal output groups every requirement by tier and prints its aggregated status, followed by per-tier counts and a
`VERDICT: CONFORMANT` / `VERDICT: NOT CONFORMANT (...)` line. `--report-json PATH` writes the same information as JSON,
plus failure diagnostics:

- `agent_command`, `agent_info`, `agent_capabilities`, `protocol_version`, `schema_revision`, `tck_version`,
  `started_at`/`finished_at`.
- `requirements`: one entry per requirement, always - including ones no test ever ran (`status: "NOT_TESTED"`) - with
  its tier, spec citation, aggregated status, and every bound test's outcome (`nodeid`, `status`, `message`,
  `duration_s`, `properties`). A `FAIL` outcome additionally carries `transcript` (the full wire traffic for that test)
  and `stderr` (truncated to the last 20 kB), so a failure is diagnosable from the JSON alone.
- `verdict`: `{"conformant": bool, "blocked_by_auth": bool, "blocked_by_version_mismatch": bool, "tier_counts": {...}}`.

## The tier / status / verdict model

(The contract for how requirements are named, tiered and counted is in [`docs/requirements.md`](docs/requirements.md).)

### Tier

Every requirement has a **tier**

#### MANDATORY

A spec MUST. A failure or an untested `MANDATORY` requirement makes the run non-conformant.

#### CAPABILITY

Only applies if the agent advertised the relevant capability in `initialize`; otherwise it's reported
`SKIPPED` ("not applicable"), which does **not** affect conformance. If the agent *did* advertise it, though, a failure
does count against conformance - advertised capabilities must work.

#### ADVISORY

A spec SHOULD. Always reported, never affects the verdict.

#### INFORMATIONAL

Spec silent, or reference implementations disagree. The test never asserts on the probed behaviour itself; it records
what was observed via `record_property`, and that note is surfaced alongside the status in both the terminal table (e.g.
`ACP-INFO-PARSE-001   PASS  (silent; conn after: usable (sessionId=...))`) and the JSON report's
`properties` field. It can still `FAIL` if the prerequisite handshake it rides on top of (e.g. `initialize`, or the
`session/new` a probe needs) itself fails - that is a real conformance problem the probe correctly surfaces, not a
probe bug. Never affects the verdict either way.

### Status

Each test produces one of `PASS` / `FAIL` / `SKIPPED`; a setup/teardown error (including a harness-level agent timeout
or crash) is reported as `FAIL`. A requirement's status is the worst across every test bound to it (`FAIL` > `PASS` >
`SKIPPED`); a requirement no test ever ran is `NOT_TESTED` - deliberately counted as a failure for the `MANDATORY` tier
(see "Verdict" below), so a dead agent that never gets past `initialize` can't score 100% by starving every other check
of a record.

### Verdict

`conformant` is `true` iff there is no `MANDATORY` `FAIL`, no `MANDATORY` `NOT_TESTED`, no `CAPABILITY`
`FAIL`, the run was not `blocked_by_auth` (i.e. no session-dependent test was skipped because the agent requires
authentication and no `--auth-method` was given - see ["Options"](#options) above), and not
`blocked_by_version_mismatch` (i.e. no version-dependent test was skipped because the agent under test never actually
negotiated the `--protocol-version` this run targets - checked for both v1 and v2 runs).

### Exit code

`0` iff `conformant`, `1` otherwise (including "the agent never responded to anything" - every
`MANDATORY` requirement ends up `FAIL`/`NOT_TESTED`, but the run still completes and still writes a report). No agent
command after `--` is a usage error (`2`).

## Protocol scope

The codebase is structured as a version-agnostic core plus one package per protocol version (`src/tck/common/` +
`src/tck/v1/` + `src/tck/v2/`, see [`docs/development.md`](docs/development.md#layout)), so each version's suite does
not require forking the harness, report model, or pytest plugin. ACP **v1** is the default. ACP **v2** is available
via `--protocol-version 2`. For the precise, current requirement set, `src/tck/v{1,2}/requirements.py` is the source
of truth.

## What is covered

### v1

v1 is checked against the upstream *draft* v1 schema (the unstable superset, including RFD-gated fields and methods).
Those extras are optional for agents, but are validated against the draft shapes when used. The schema is pinned to the
spec commit recorded in `src/tck/v1/schema/VENDORED.md`.

- `initialize` handshake and version negotiation, including the unsupported-version probe (`ACP-INIT-003`)
- Session lifecycle: `session/new` (including stdio MCP servers: accepted and connected to), `session/load`,
  `session/resume`, `session/list`, `session/delete`, `session/close`, `session/archive`/`unarchive`,
  `additionalDirectories`, `systemPrompt`
- `session/prompt` turns and `session/cancel`, including the cancellation race handling described above
- Session `modes` and `configOptions`
- Prompt content capabilities (`image`/`audio`/`embeddedContext`)
- Permission requests (a rejected or unrecognised answer is not approval) and plan updates
- Authentication surface: `authMethods` (including `terminal` methods when the client enables them), `authenticate`,
  `logout`, `auth/status`
- Client-capability negatives: the agent must never call `fs/*`, `terminal/*`, or `elicitation/create`, or send
  notice, compaction, plan or subagent updates, when the client didn't advertise the matching capability
  (`ACP-CLIENTCAP-001`..`007`)
- Subagents (unstable): over a connection that advertises `clientCapabilities.subagents`, an agent that exposes a
  child must announce it before any traffic for it, keep the association and `session` references consistent, report
  absolute directories and schema-valid state (`ACP-SUBAGENT-*`; they SKIP when the agent exposes no child)
- Error codes: unknown sessions, requests before `initialize`, unadvertised methods, unknown modes and config values,
  reserved-range codes
- Extensibility and hygiene: `_`-prefixed custom methods must get a response (`ACP-EXT-001`), custom notifications
  are ignored, `_meta` passthrough, unknown top-level keys (including on error objects), error message shape and
  `-32602` for invalid params
- Transport/JSON-RPC hygiene: stdio framing, envelope validation, unrecognised-method handling, no replies to
  notifications, `$/cancel_request` (unknown ids, and an in-flight `session/prompt`)
- `INFORMATIONAL` probes (reported only, spec silent or reference agents disagree): malformed JSON, structurally-invalid
  requests, stderr volume, shutdown promptness
- Not yet covered: the agent's use of advertised `fs/*` and `terminal/*` client capabilities (only the negatives
  above)

### v2

v2 is checked against the upstream *draft* schema (the unstable superset, including RFD-gated fields and methods). Those
extras are optional for agents, but are validated against the draft shapes when used. The schema is pinned to the spec
commit recorded in `src/tck/v2/schema/VENDORED.md`.

- `initialize` and version negotiation, including a v2-only agent's required behavior when asked for `1`, and the
  initialization rules (requests before `initialize`, repeated `initialize`)
- `session/new` baseline, MCP server config, `additionalDirectories`, `systemPrompt`
- Core `session/prompt` turn/`state_update` lifecycle (turn completion via `state_update`, not the prompt response),
  prompts sent during active work, and background work lists
- `session/cancel` (confirmed via a terminating `cancelled` idle `state_update`), including a turn blocked on a
  permission request, and `$/cancel_request`
- Prompt content capabilities (`image`/`audio`/`embeddedContext`), and rejection of unknown or unadvertised content
- `session/request_permission` flow and tool-call status rules
- Agent -> client method rules (including the `_`/`$/`-prefix extensibility rule)
- stdio transport and the JSON-RPC envelope (request ids, no batching: JSON arrays are rejected)
- Session management: `session/resume` (including replay ordering), `session/list`, `session/close`/`delete`,
  `session/fork`, `session/archive`/`unarchive`, `session/set_config_option`/`configOptions`, slash commands
- Authentication: `authMethods`, `auth/login`/`auth/logout`, `auth/status`
- Keyed upsert/patch semantics (messages, tool calls, terminals), open-enum emitter rules (custom values must be `_`
  -prefixed)
- Error codes (unknown sessions, unadvertised methods, reserved ranges), extensibility/`_meta` (including trace
  context keys), schema hygiene, error shape, shutdown promptness
- `INFORMATIONAL` probes: malformed JSON, structurally-invalid requests, stderr volume, whether stdio/http MCP servers
  are accepted, how a prompt sent during active work is handled, and `session/cancel` with no foreground work

## Contributing / docs

Contributor docs are in [`docs/`](docs/README.md): repo layout, setup and conventions; requirement ids, tiers and
citation rules; how to add a requirement and its test; the mock-client prompt driver; the harness API; and how to
update the TCK to a new spec revision. Coding agents also read [`AGENTS.md`](AGENTS.md).
