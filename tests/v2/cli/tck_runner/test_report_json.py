"""End-to-end tests of `acp-tck` itself: the `--report-json` report."""

from __future__ import annotations

import json

from .._runner import FIXTURES_DIR_V2, _run_cli


def test_v2_report_json_reads_the_v2_shaped_initialize_result(tmp_path):
    """`--report-json` for a real v2 run must carry `protocol_version == 2` and read
    `agent_info`/`agent_capabilities` from the v2-renamed `info`/`capabilities` keys
    (`tck.common.version.VersionSpec.agent_info_field`/`agent_capabilities_field` -- see
    `tests/common/test_version.py` for the mechanism itself in isolation)."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2, "conforming.py", protocol_version=2, report_json=str(report_path)
    )
    assert result.returncode == 0, result.stdout + result.stderr

    report = json.loads(report_path.read_text())
    assert report["protocol_version"] == 2
    assert report["agent_info"] == {"name": "tck-fixture-conforming-v2", "version": "0.0.0"}
    assert report["agent_capabilities"] == {"session": {}}
    assert report["verdict"]["conformant"] is True
