"""Guard: `@pytest.mark.capability` only takes real `initialize`-result paths.

An `inferred:<feature>` string is documentation only (`docs/requirements.md#inferredfeature-gates`):
`capability_is_supported` finds no such path, so a marked test would SKIP on every agent and the
run would false-PASS.
"""

from __future__ import annotations

import ast
from pathlib import Path

import tck

_SRC = Path(tck.__file__).parent


def inferred_capability_markers(source: str) -> list[int]:
    """Line numbers of `capability("inferred:...")` calls (as `pytest.mark.capability(...)`)."""
    return [
        node.lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "capability"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
        and node.args[0].value.startswith("inferred:")
    ]


def test_detector_flags_an_inferred_path_in_the_marker():
    bad = '@pytest.mark.capability("inferred:subagents")\nasync def test_x(): ...\n'
    good = '@pytest.mark.capability("agentCapabilities.loadSession", boolean=True)\nasync def test_x(): ...\n'
    assert inferred_capability_markers(bad) == [1]
    assert inferred_capability_markers(good) == []


def test_no_conformance_test_gates_on_an_inferred_path():
    offenders = [
        f"{path.relative_to(_SRC)}:{line}"
        for path in sorted(_SRC.glob("v*/conformance/*.py"))
        for line in inferred_capability_markers(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, (
        "`inferred:` paths are documentation-only; the test must pytest.skip itself instead: "
        + ", ".join(offenders)
    )
