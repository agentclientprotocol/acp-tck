"""Meta-tests over `tck.v2.requirements.REGISTRY`: shape invariants, plus a two-way check against
every `@pytest.mark.requirement(...)` used under `src/tck/v2/conformance/` (import the modules
and inspect `pytestmark` directly -- no grep). Mirrors `tests/v1/test_registry.py`.

See `tck.v2.requirements`'s module docstring for the id-namespacing decisions (e.g. why
`ACP-CLOSE-202` reuses `ACP-CANCEL-208`'s test instead of adding a second probe).
"""

from __future__ import annotations

import importlib
import json
import pkgutil
import re
from pathlib import Path
from typing import Any

import pytest

from tck.common.requirements import Tier
from tck.v2.protocol import SCHEMA_DIR, SCHEMA_REVISION
from tck.v2 import requirements as req_module
from tck.v2.requirements import REGISTRY

_ID_PATTERN = re.compile(r"^ACP-[A-Z]+(?:-[A-Z]+)*-\d{3}$")
_SPEC_REVISION_PATTERN = re.compile(r"@ [0-9a-f]{40}$")


def test_ids_are_unique_and_well_formed():
    ids = list(REGISTRY)
    assert len(ids) == len(set(ids)), "duplicate requirement ids in REGISTRY"
    for req_id, requirement in REGISTRY.items():
        assert req_id == requirement.id
        assert _ID_PATTERN.match(req_id), f"{req_id!r} does not match ACP-<AREA>-<NNN>"


def test_registry_has_exactly_the_expected_requirements():
    """Notable non-obvious ids: `ACP-PATCH-202` and the re-worded `ACP-PROMPT-001` are
    deliberately not registered -- duplicates of `ACP-PROMPT-201`/`ACP-PROMPT-203` and
    `ACP-STATE-203` respectively. `ACP-AUTH-203` (CAPABILITY) replaces v1's `ACP-AUTH-004`
    outright -- v2 has no logout capability marker. See `tck.v2.requirements`'s module docstring
    for the full id-namespacing rationale."""
    assert set(REGISTRY) == {
        "ACP-INIT-001",
        "ACP-INIT-003",
        "ACP-INIT-201",
        "ACP-INIT-202",
        "ACP-INIT-203",
        "ACP-INIT-204",
        "ACP-SCHEMA-001",
        "ACP-SESSION-001",
        "ACP-SESSION-002",
        "ACP-PROMPT-205",
        "ACP-PROMPT-201",
        "ACP-PROMPT-203",
        "ACP-STATE-201",
        "ACP-STATE-202",
        "ACP-STATE-203",
        "ACP-PROMPTCAP-001",
        "ACP-PROMPTCAP-002",
        "ACP-PROMPTCAP-003",
        "ACP-PROMPT-003",
        "ACP-PERM-201",
        "ACP-CLIENTCAP-201",
        "ACP-CLIENTCAP-202",
        "ACP-INFO-CONCURRENT-201",
        "ACP-INFO-UNKNOWNSESSION-001",
        "ACP-TRANSPORT-201",
        "ACP-TRANSPORT-002",
        "ACP-TRANSPORT-203",
        "ACP-JSONRPC-001",
        "ACP-JSONRPC-002",
        "ACP-JSONRPC-003",
        "ACP-JSONRPC-004",
        "ACP-JSONRPC-005",
        "ACP-BATCH-201",
        "ACP-BATCH-202",
        "ACP-BATCH-203",
        "ACP-BATCH-204",
        "ACP-BATCH-205",
        "ACP-BATCH-206",
        "ACP-BATCH-207",
        "ACP-BATCH-208",
        "ACP-CANCEL-201",
        "ACP-CANCEL-202",
        "ACP-CANCEL-203",
        "ACP-CANCEL-204",
        "ACP-CANCEL-205",
        "ACP-CANCEL-206",
        "ACP-CANCEL-207",
        "ACP-CANCEL-208",
        "ACP-INFO-BATCH-201",
        "ACP-INFO-BATCH-202",
        "ACP-INFO-CANCEL-201",
        "ACP-INFO-CANCEL-202",
        "ACP-SESSION-203",
        "ACP-RESUME-201",
        "ACP-RESUME-202",
        "ACP-RESUME-203",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-LIST-201",
        "ACP-LIST-202",
        "ACP-LIST-203",
        "ACP-LIST-204",
        "ACP-CLOSE-201",
        "ACP-CLOSE-202",
        "ACP-DELETE-201",
        "ACP-DELETE-202",
        "ACP-DELETE-203",
        "ACP-ADDDIRS-201",
        "ACP-ADDDIRS-202",
        "ACP-MCP-201",
        "ACP-MCP-202",
        "ACP-CONFIG-201",
        "ACP-CONFIG-202",
        "ACP-CONFIG-203",
        "ACP-CONFIG-204",
        "ACP-CONFIG-206",
        "ACP-AUTH-201",
        "ACP-AUTH-202",
        "ACP-AUTH-203",
        "ACP-AUTH-204",
        "ACP-AUTH-205",
        "ACP-AUTH-206",
        "ACP-AUTH-207",
        "ACP-PATCH-201",
        "ACP-PATCH-203",
        "ACP-PATCH-204",
        "ACP-PATCH-205",
        "ACP-PATCH-206",
        "ACP-PATCH-207",
        "ACP-PATCH-208",
        "ACP-PATCH-209",
        "ACP-ENUM-201",
        "ACP-ENUM-202",
        "ACP-ENUM-203",
        "ACP-META-001",
        "ACP-META-201",
        "ACP-EXT-001",
        "ACP-EXT-201",
        "ACP-EXT-202",
        "ACP-EXT-203",
        "ACP-ERROR-001",
        "ACP-SHUTDOWN-001",
        "ACP-SCHEMA-002",
        "ACP-STDERR-001",
        "ACP-INFO-PARSE-001",
        "ACP-INFO-INVALIDREQ-001",
    }


def test_advisory_tier_is_exactly_these_ids():
    """Pins the ADVISORY set: without this, the registry meta-tests would only check shape
    invariants and never actual tier membership, so a re-tiering mistake could silently regress
    without any test catching it."""
    assert {req.id for req in REGISTRY.values() if req.tier is Tier.ADVISORY} == {
        "ACP-AUTH-201",
        "ACP-AUTH-205",
        "ACP-BATCH-203",
        "ACP-BATCH-204",
        "ACP-BATCH-205",
        "ACP-DELETE-203",
        "ACP-ENUM-202",
        "ACP-ENUM-203",
        "ACP-ERROR-001",
        "ACP-EXT-201",
        "ACP-EXT-202",
        "ACP-JSONRPC-004",
        "ACP-JSONRPC-005",
        "ACP-META-001",
        "ACP-META-201",
        "ACP-PATCH-208",
        "ACP-PATCH-209",
        "ACP-PROMPT-003",
        "ACP-SCHEMA-002",
        "ACP-SHUTDOWN-001",
    }


def test_informational_tier_is_exactly_these_ids():
    """Pins the INFORMATIONAL set -- see `test_advisory_tier_is_exactly_these_ids` above.
    `ACP-BATCH-206/207/208` and `ACP-CANCEL-204` are here (not ADVISORY): each is always SKIPped,
    never PASS/FAIL, so they belong in the record-only tier."""
    assert {req.id for req in REGISTRY.values() if req.tier is Tier.INFORMATIONAL} == {
        "ACP-BATCH-206",
        "ACP-BATCH-207",
        "ACP-BATCH-208",
        "ACP-CANCEL-204",
        "ACP-EXT-203",
        "ACP-INFO-BATCH-201",
        "ACP-INFO-BATCH-202",
        "ACP-INFO-CANCEL-201",
        "ACP-INFO-CANCEL-202",
        "ACP-INFO-CONCURRENT-201",
        "ACP-INFO-INVALIDREQ-001",
        "ACP-INFO-PARSE-001",
        "ACP-INFO-UNKNOWNSESSION-001",
        "ACP-MCP-201",
        "ACP-MCP-202",
        "ACP-STDERR-001",
    }


def test_capability_field_set_iff_capability_tier():
    for requirement in REGISTRY.values():
        if requirement.tier is Tier.CAPABILITY:
            assert requirement.capability, f"{requirement.id} is CAPABILITY but has no capability path"
        else:
            assert requirement.capability is None, (
                f"{requirement.id} is tier {requirement.tier.value}, not CAPABILITY, but has "
                f"capability={requirement.capability!r}"
            )


def test_text_and_citation_are_non_empty():
    for requirement in REGISTRY.values():
        assert requirement.text.strip(), f"{requirement.id} has empty text"
        assert requirement.citation.strip(), f"{requirement.id} has empty citation"


def test_citation_mentions_a_spec_revision_hash():
    for requirement in REGISTRY.values():
        assert _SPEC_REVISION_PATTERN.search(requirement.citation), (
            f"{requirement.id}'s citation does not end in '@ <40-hex-char spec revision>': "
            f"{requirement.citation!r}"
        )
        assert SCHEMA_REVISION in requirement.citation, (
            f"{requirement.id}'s citation is not pinned to tck.v2.protocol.SCHEMA_REVISION: "
            f"{requirement.citation!r}"
        )


def test_get_raises_helpful_key_error_for_unknown_id():
    with pytest.raises(KeyError, match="not a registered requirement id"):
        req_module.get("ACP-NOPE-999")


def test_get_returns_the_registered_requirement():
    any_id = next(iter(REGISTRY))
    assert req_module.get(any_id) is REGISTRY[any_id]


def _requirement_ids_used_in_conformance_tests() -> set[str]:
    import tck.v2.conformance as conformance_pkg

    used: set[str] = set()
    for module_info in pkgutil.iter_modules(conformance_pkg.__path__, conformance_pkg.__name__ + "."):
        leaf_name = module_info.name.rsplit(".", 1)[-1]
        if not leaf_name.startswith("test_"):
            continue
        module = importlib.import_module(module_info.name)
        for name, obj in vars(module).items():
            if not name.startswith("test_") or not callable(obj):
                continue
            for mark in getattr(obj, "pytestmark", []):
                if mark.name == "requirement":
                    used.update(mark.args)
    return used


def test_every_requirement_marker_id_exists_in_the_registry():
    used_ids = _requirement_ids_used_in_conformance_tests()
    unknown = used_ids - set(REGISTRY)
    assert not unknown, f"@pytest.mark.requirement id(s) not in REGISTRY: {sorted(unknown)}"


def test_every_registry_id_is_referenced_by_at_least_one_test():
    used_ids = _requirement_ids_used_in_conformance_tests()
    missing = set(REGISTRY) - used_ids
    assert not missing, f"REGISTRY id(s) with no @pytest.mark.requirement anywhere: {sorted(missing)}"


def test_cli_selftest_tier_sets_match_the_registry():
    """v2 twin of `tests/v1/test_registry.py::test_cli_selftest_tier_sets_match_the_registry`:
    `tests/v2/test_cli.py` hand-maintains `_MANDATORY_IDS`/`_CAPABILITY_IDS`, which must mirror
    `REGISTRY`'s own `Tier` field exactly -- otherwise a tier misclassification could go
    unnoticed. `tests/v2` is a package (unlike `tests/v1`), so the sibling module is imported as
    `v2.test_cli`, not the bare `test_cli` v1 uses -- see `AGENTS.md`'s `tests/v2/__init__.py`
    layout note."""
    import v2.test_cli as test_cli

    by_tier: dict[Tier, set[str]] = {tier: set() for tier in Tier}
    for req_id, requirement in REGISTRY.items():
        by_tier[requirement.tier].add(req_id)

    assert test_cli._MANDATORY_IDS == by_tier[Tier.MANDATORY], (
        test_cli._MANDATORY_IDS ^ by_tier[Tier.MANDATORY]
    )
    assert test_cli._CAPABILITY_IDS == by_tier[Tier.CAPABILITY], (
        test_cli._CAPABILITY_IDS ^ by_tier[Tier.CAPABILITY]
    )


# --- schema citations ------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_V2_SOURCE_DIRS = (
    _REPO_ROOT / "src" / "tck" / "v2",
    _REPO_ROOT / "tests" / "v2",
    _REPO_ROOT / "tests" / "fixtures" / "agents" / "v2",
)
_POINTER_PATTERN = re.compile(r"schema\.unstable\.json#(/[^\s`'\"),;]*)")
# Any mention of the stable file names; `schema.unstable.json` does not match.
_STABLE_NAME_PATTERN = re.compile(r"\b(?:schema|meta)\.json\b")


def _resolve_pointer(document: Any, pointer: str) -> Any:
    """RFC 6901 resolution; raises `KeyError`/`IndexError`/`ValueError` if it does not resolve."""
    node = document
    for raw in pointer.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict):
            node = node[token]
        elif isinstance(node, list):
            if not token.isdigit() or (token != "0" and token.startswith("0")):
                raise ValueError(f"bad array index {token!r}")
            node = node[int(token)]
        else:
            raise KeyError(token)
    return node


def _v2_source_files() -> list[Path]:
    this_file = Path(__file__).resolve()
    return sorted(
        path
        for root in _V2_SOURCE_DIRS
        for path in root.rglob("*.py")
        if path.resolve() != this_file and "__pycache__" not in path.parts
    )


def _schema_pointers_by_source() -> dict[str, list[str]]:
    sources = {
        f"{req_id} citation": requirement.citation for req_id, requirement in REGISTRY.items()
    }
    for path in _v2_source_files():
        sources[str(path.relative_to(_REPO_ROOT))] = path.read_text()
    return {
        name: [m.rstrip(".") for m in _POINTER_PATTERN.findall(text)] for name, text in sources.items()
    }


def _unresolved_pointers(pointers_by_source: dict[str, list[str]], schema: Any) -> list[str]:
    bad = []
    for source, pointers in pointers_by_source.items():
        for pointer in pointers:
            try:
                _resolve_pointer(schema, pointer)
            except (KeyError, IndexError, ValueError):
                bad.append(f"{source}: {pointer}")
    return bad


def test_resolve_pointer_handles_escapes_and_arrays():
    doc = {"a/b": {"c~d": [10, {"x": 1}]}}
    assert _resolve_pointer(doc, "/a~1b/c~0d/1/x") == 1
    assert _resolve_pointer(doc, "") is doc
    for bad in ("/a~1b/c~0d/2", "/a~1b/c~0d/01", "/a/b", "/a~1b/c~0d/x"):
        with pytest.raises((KeyError, IndexError, ValueError)):
            _resolve_pointer(doc, bad)


def test_schema_citation_pointers_resolve_in_the_vendored_schema():
    schema = json.loads((SCHEMA_DIR / "schema.unstable.json").read_text())
    pointers_by_source = _schema_pointers_by_source()
    assert sum(len(v) for v in pointers_by_source.values()) > 50, "pointer extraction found too few"
    assert not _unresolved_pointers(pointers_by_source, schema)


def test_unresolvable_pointer_is_reported():
    schema = json.loads((SCHEMA_DIR / "schema.unstable.json").read_text())
    broken = {"x": ["/$defs/StopReason", "/$defs/NoSuchDef", "/$defs/StopReason/anyOf/99"]}
    assert _unresolved_pointers(broken, schema) == ["x: /$defs/NoSuchDef", "x: /$defs/StopReason/anyOf/99"]


def test_no_v2_source_mentions_the_stable_schema_files():
    offenders = [
        str(path.relative_to(_REPO_ROOT))
        for path in _v2_source_files()
        if _STABLE_NAME_PATTERN.search(path.read_text())
    ]
    assert not offenders, f"v2 files mention stable schema.json/meta.json: {offenders}"
    for requirement in REGISTRY.values():
        assert not _STABLE_NAME_PATTERN.search(requirement.citation), requirement.id


# Prose citations point at the draft doc tree, matching the draft schema.
_NON_DRAFT_DOCS_PATTERN = re.compile(r"docs/protocol/v2/(?!draft/)")


def test_no_v2_source_cites_the_non_draft_docs_tree():
    offenders = [
        str(path.relative_to(_REPO_ROOT))
        for path in _v2_source_files()
        if _NON_DRAFT_DOCS_PATTERN.search(path.read_text())
    ]
    assert not offenders, f"v2 files cite docs/protocol/v2/ outside draft/: {offenders}"
    for requirement in REGISTRY.values():
        assert not _NON_DRAFT_DOCS_PATTERN.search(requirement.citation), requirement.id
        assert not _NON_DRAFT_DOCS_PATTERN.search(requirement.text), requirement.id
