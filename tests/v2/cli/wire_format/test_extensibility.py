"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_extensibility.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _fails, _negotiation_fails, _run_cli, _table_statuses


def test_calls_custom_method_passes_everything_it_can():
    """Positive control for the `_`-prefix open-enum rule on agent -> client methods, paired
    with `calls_fs_unadvertised.py`'s negative control. Advertises only the plain `session: {}}`
    baseline, so `ACP-PROMPTCAP-001/002/003`/`ACP-PERM-201` still SKIP -- this fixture is a
    control for `ACP-CLIENTCAP-003/202` specifically, not a full `conforming_full.py`-style
    all-PASS fixture. The exit code/overall verdict text are not asserted here: this run is
    `-k`-scoped, which necessarily leaves every other MANDATORY id NOT_TESTED, and NOT_TESTED
    MANDATORY ids do flip the verdict to NOT CONFORMANT by design (see
    v1's `test_hangs_until_cancel_agent_passes_cancel_requirements` for the
    same precedent) -- that says nothing about whether *this* fixture's behaviour for the ids
    actually exercised is conforming, which is what the per-id statuses below check."""
    result = _run_cli(
        FIXTURES_DIR_V2, "calls_custom_method.py", protocol_version=2, k="client_capabilities"
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    assert statuses.get("ACP-CLIENTCAP-003") == "PASS", result.stdout
    assert statuses.get("ACP-CLIENTCAP-202") == "PASS", result.stdout


def test_rejects_unknown_capability_fields_fails_ext_204_only():
    fails, statuses = _negotiation_fails("rejects_unknown_capability_fields.py")
    assert fails == {"ACP-EXT-204"}, statuses


def test_v2_exit_on_malformed_mcp_message_fails_ext_002_only():
    """`exits_on_malformed_mcp_message.py` does not advertise `capabilities.session.mcp.acp` and
    exits on an `mcp/message` notification missing `requestId`. It sent no reply, so
    `ACP-JSONRPC-003` PASSes (v1 agrees); the crash on a notification it does not recognize is
    `ACP-EXT-002`'s finding."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "exits_on_malformed_mcp_message.py",
        protocol_version=2,
        k="jsonrpc or extensibility",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-EXT-002"}, result.stdout
    assert statuses.get("ACP-JSONRPC-003") == "PASS", result.stdout


def test_v2_acp_advertising_agent_is_not_sent_the_ext_002_mcp_probe():
    """`answers_mcp_notification.py` advertises `capabilities.session.mcp.acp`, so
    `ACP-EXT-002`'s `mcp/message` probe is skipped for it; the `_tck/ping` probe still PASSes the
    row."""
    result = _run_cli(
        FIXTURES_DIR_V2, "answers_mcp_notification.py", protocol_version=2, k="extensibility"
    )
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-EXT-002") == "PASS", result.stdout


def _extensibility_run(fixture: str):
    return _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_extensibility")


def test_answers_unknown_protocol_notification_fails_ext_203_only():
    """`answers_unknown_protocol_notification.py` replies to an unrecognized `$/` notification
    (SHOULD be ignored): `ACP-EXT-203` FAILs; the `_`-prefixed notification of `ACP-EXT-002` is
    left alone."""
    result = _extensibility_run("answers_unknown_protocol_notification.py")
    assert _fails(_table_statuses(result.stdout)) == {"ACP-EXT-203"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-EXT-002") == "PASS", result.stdout


def test_rejects_malformed_meta_fails_meta_202_only():
    """`rejects_malformed_meta.py` answers a prompt with a non-object `_meta` with `-32602`
    instead of treating it as omitted: `ACP-META-202` FAILs, `ACP-META-001` (object `_meta`)
    still PASSes."""
    result = _extensibility_run("rejects_malformed_meta.py")
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-META-202"}, result.stdout
    assert statuses.get("ACP-META-001") == "PASS", result.stdout


def test_malformed_traceparent_fails_meta_203_only():
    """`malformed_traceparent.py` emits `_meta: {"traceparent": "not-a-trace-id"}`:
    `ACP-META-203` FAILs. The key itself is a reserved W3C one, so `ACP-META-204` PASSes."""
    result = _extensibility_run("malformed_traceparent.py")
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-META-203"}, result.stdout
    assert statuses.get("ACP-META-204") == "PASS", result.stdout


def test_unprefixed_meta_key_fails_meta_204_only():
    """`unprefixed_meta_key.py` advertises `capabilities._meta: {"vendorThing": true}`:
    only the ADVISORY `ACP-META-204` FAILs, so the verdict stays CONFORMANT."""
    result = _extensibility_run("unprefixed_meta_key.py")
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-META-204"}, result.stdout
    assert statuses.get("ACP-META-203") == "SKIPPED", result.stdout


def test_emits_w3c_meta_passes_meta_203_and_204():
    """Positive control: valid W3C trace keys and reverse-DNS namespaced keys really are
    observed, so both rows PASS rather than SKIP."""
    result = _extensibility_run("emits_w3c_meta.py")
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    assert statuses.get("ACP-META-203") == "PASS", result.stdout
    assert statuses.get("ACP-META-204") == "PASS", result.stdout


def test_custom_method_no_response_fails_ext_001_and_error_001():
    """`custom_method_no_response.py` silently swallows every `_`-prefixed custom method
    request instead of responding at all -- FAILs `ACP-EXT-001` (MANDATORY) directly. It also
    cascades into the ADVISORY `ACP-ERROR-001` (`test_diagnostics.py`): that probe sends its own
    `_`-prefixed unknown method and, getting no reply at all instead of a `-32601` with a
    non-empty one-line `message`, FAILs the "error message is well-formed" check outright.
    Within `test_initialize or test_extensibility or test_diagnostics` those are the only FAILs:
    the INIT rows that probe with an unknown `_tck/...` request (`ACP-INIT-211`/`212`/`213`)
    treat silence as no evidence. `ACP-BATCH-209`'s array probes are rejected whole, never
    dispatched per element, so it is unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "custom_method_no_response.py",
        protocol_version=2,
        k="test_initialize or test_extensibility or test_diagnostics",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-EXT-001", "ACP-ERROR-001"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_unknown_root_key_fails_schema_002_only():
    """`unknown_root_key.py` adds `unknownRootKey` to the `initialize` result's root -- FAILs
    `ACP-SCHEMA-002` (ADVISORY) only; the vendored schema itself never sets
    `additionalProperties: false`, so this is not caught by `ACP-SCHEMA-001`/`ACP-INIT-001`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "unknown_root_key.py", protocol_version=2, k="test_extensibility or initialize"
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SCHEMA-002"}, result.stdout


def test_unknown_capability_root_key_fails_ext_202():
    """`unknown_capability_root_key.py` adds `capabilities.vendorFeature`, which has no home in
    the schema -- `ACP-EXT-202` must still FAIL for a genuinely unrecognized `capabilities`
    root key."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "unknown_capability_root_key.py",
        protocol_version=2,
        k="test_extensibility or initialize",
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-EXT-202"}, result.stdout
