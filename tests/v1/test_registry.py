"""Meta-tests over `tck.v1.requirements.REGISTRY`: shape invariants, plus a two-way check against
every `@pytest.mark.requirement(...)` used under `src/tck/v1/conformance/` (import the modules
and inspect `pytestmark` directly -- no grep, per the task spec).
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
from tck.common.spec_map import SectionError, parse_spec_map, resolve_section
from tck.v1.protocol import SCHEMA_DIR, SCHEMA_REVISION
from tck.v1 import requirements as req_module
from tck.v1 import spec_map as spec_map_module
from tck.v1.requirements import REGISTRY

_ID_PATTERN = re.compile(r"^ACP-[A-Z]+(?:-[A-Z]+)*-\d{3}$")
"""`ACP-<AREA>-<NNN>`, where `<AREA>` may itself be hyphen-segmented (e.g.
`ACP-INFO-PARSE-001`, `ACP-INFO-UNKNOWNSESSION-001`) -- the INFORMATIONAL-tier ids group under a
shared `ACP-INFO-*` prefix rather than inventing an unrelated area name per id, since they are a
related family of "record, never assert" probes (see
`tck/v1/conformance/test_informational.py`)."""
_SPEC_REVISION_PATTERN = re.compile(r"@ [0-9a-f]{40}$")


def test_ids_are_unique_and_well_formed():
    ids = list(REGISTRY)
    assert len(ids) == len(set(ids)), "duplicate requirement ids in REGISTRY"
    for req_id, requirement in REGISTRY.items():
        assert req_id == requirement.id
        assert _ID_PATTERN.match(req_id), f"{req_id!r} does not match ACP-<AREA>-<NNN>"


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
            f"{requirement.id}'s citation is not pinned to tck.v1.protocol.SCHEMA_REVISION: "
            f"{requirement.citation!r}"
        )


def test_get_raises_helpful_key_error_for_unknown_id():
    with pytest.raises(KeyError, match="not a registered requirement id"):
        req_module.get("ACP-NOPE-999")


def test_get_returns_the_registered_requirement():
    any_id = next(iter(REGISTRY))
    assert req_module.get(any_id) is REGISTRY[any_id]


def _requirement_ids_used_in_conformance_tests() -> set[str]:
    import tck.v1.conformance as conformance_pkg

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
    """`tests/v1/test_cli.py` hand-maintains four id sets
    (`_MANDATORY_IDS`/`_ADVISORY_IDS`/`_INFORMATIONAL_IDS`/`_CAPABILITY_IDS`) that must mirror
    `REGISTRY`'s own `Tier` field exactly -- this caught the AUTH-001/AUTH-003 retiering
    silently going stale in `test_cli.py` when `requirements.py`'s tier changed. Deriving the
    sets directly from `REGISTRY` instead was considered and rejected: `test_cli.py`'s sets
    exist to state, by hand, the expected status of every id against `conforming.py`/
    `conforming_full.py`, which is a stronger check than "the tier field matches" -- so this
    test cross-checks the two independently-written sources instead of collapsing them into
    one."""
    import test_cli

    by_tier: dict[Tier, set[str]] = {tier: set() for tier in Tier}
    for req_id, requirement in REGISTRY.items():
        by_tier[requirement.tier].add(req_id)

    assert test_cli._MANDATORY_IDS == by_tier[Tier.MANDATORY], (
        test_cli._MANDATORY_IDS ^ by_tier[Tier.MANDATORY]
    )
    assert test_cli._ADVISORY_IDS == by_tier[Tier.ADVISORY], (
        test_cli._ADVISORY_IDS ^ by_tier[Tier.ADVISORY]
    )
    assert test_cli._INFORMATIONAL_IDS == by_tier[Tier.INFORMATIONAL], (
        test_cli._INFORMATIONAL_IDS ^ by_tier[Tier.INFORMATIONAL]
    )
    assert test_cli._CAPABILITY_IDS == by_tier[Tier.CAPABILITY], (
        test_cli._CAPABILITY_IDS ^ by_tier[Tier.CAPABILITY]
    )


# --- schema citations ------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_V1_SOURCE_DIRS = (
    _REPO_ROOT / "src" / "tck" / "v1",
    _REPO_ROOT / "tests" / "v1",
    _REPO_ROOT / "tests" / "fixtures" / "agents" / "v1",
)
# v1 pointers only; a v1 file may cite v2's schema (`schema/v2/schema.unstable.json#...`).
_POINTER_PATTERN = re.compile(r"(?<!v2/)schema\.unstable\.json#(/[^\s`'\"),;]*)")
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


def _v1_source_files() -> list[Path]:
    this_file = Path(__file__).resolve()
    return sorted(
        path
        for root in _V1_SOURCE_DIRS
        for path in root.rglob("*.py")
        if path.resolve() != this_file and "__pycache__" not in path.parts
    )


def _schema_pointers_by_source() -> dict[str, list[str]]:
    sources = {
        f"{req_id} citation": requirement.citation for req_id, requirement in REGISTRY.items()
    }
    for path in _v1_source_files():
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


def test_pointer_pattern_skips_v2_schema_citations():
    text = "schema/v1/schema.unstable.json#/$defs/A; schema/v2/schema.unstable.json#/$defs/B"
    assert _POINTER_PATTERN.findall(text) == ["/$defs/A"]


def test_schema_citation_pointers_resolve_in_the_vendored_schema():
    schema = json.loads((SCHEMA_DIR / "schema.unstable.json").read_text())
    pointers_by_source = _schema_pointers_by_source()
    assert sum(len(v) for v in pointers_by_source.values()) > 50, "pointer extraction found too few"
    assert not _unresolved_pointers(pointers_by_source, schema)


def test_unresolvable_pointer_is_reported():
    schema = json.loads((SCHEMA_DIR / "schema.unstable.json").read_text())
    broken = {"x": ["/$defs/StopReason", "/$defs/NoSuchDef", "/$defs/StopReason/oneOf/99"]}
    assert _unresolved_pointers(broken, schema) == ["x: /$defs/NoSuchDef", "x: /$defs/StopReason/oneOf/99"]


def test_no_v1_source_mentions_the_stable_schema_files():
    offenders = [
        str(path.relative_to(_REPO_ROOT))
        for path in _v1_source_files()
        if _STABLE_NAME_PATTERN.search(path.read_text())
    ]
    assert not offenders, f"v1 files mention stable schema.json/meta.json: {offenders}"
    for requirement in REGISTRY.values():
        assert not _STABLE_NAME_PATTERN.search(requirement.citation), requirement.id


# Prose citations point at the draft doc tree, matching the draft schema.
_NON_DRAFT_DOCS_PATTERN = re.compile(r"docs/protocol/v1/(?!draft/)")


def test_no_v1_source_cites_the_non_draft_docs_tree():
    offenders = [
        str(path.relative_to(_REPO_ROOT))
        for path in _v1_source_files()
        if _NON_DRAFT_DOCS_PATTERN.search(path.read_text())
    ]
    assert not offenders, f"v1 files cite docs/protocol/v1/ outside draft/: {offenders}"
    for requirement in REGISTRY.values():
        assert not _NON_DRAFT_DOCS_PATTERN.search(requirement.citation), requirement.id
        assert not _NON_DRAFT_DOCS_PATTERN.search(requirement.text), requirement.id


# --- spec map --------------------------------------------------------------------------------

_SPEC_MAP = spec_map_module.load()
_DOC_PATH_PATTERN = re.compile(r"^docs/protocol/v1/draft/[a-z0-9-]+\.mdx$")


def _load_schema() -> Any:
    return json.loads((SCHEMA_DIR / "schema.unstable.json").read_text())


def _ledger_citation_problems(citation: str, schema: Any) -> list[str]:
    """The same rules a requirement citation is held to (revision pin, schema pointers that
    resolve, no stable schema files, no non-draft docs)."""
    problems = []
    if not _SPEC_REVISION_PATTERN.search(citation) or SCHEMA_REVISION not in citation:
        problems.append("does not end in '@ <SCHEMA_REVISION>'")
    if _STABLE_NAME_PATTERN.search(citation):
        problems.append("mentions the stable schema.json/meta.json")
    if _NON_DRAFT_DOCS_PATTERN.search(citation):
        problems.append("cites the docs tree outside draft/")
    problems += [
        f"unresolvable pointer {pointer}"
        for pointer in _unresolved_pointers(
            {"c": [m.rstrip(".") for m in _POINTER_PATTERN.findall(citation)]}, schema
        )
    ]
    return problems


def test_spec_map_core_docs_exist_at_the_pinned_revision(spec_doc):
    assert _SPEC_MAP.core_docs, "spec map lists no core docs"
    paths = [core.path for core in _SPEC_MAP.core_docs]
    assert len(paths) == len(set(paths)), "a core doc is listed twice"
    for core in _SPEC_MAP.core_docs:
        assert _DOC_PATH_PATTERN.match(core.path), core.path
        spec_doc(SCHEMA_REVISION, core.path)


def test_spec_map_core_sections_resolve_to_one_range_in_their_doc(spec_doc):
    scoped = [core for core in _SPEC_MAP.core_docs if core.sections]
    assert scoped, "expected at least one section-scoped core doc"
    for core in scoped:
        text = spec_doc(SCHEMA_REVISION, core.path)
        assert len(set(core.sections)) == len(core.sections), f"{core.path}: duplicate section"
        for section in core.sections:
            try:
                resolve_section(text, section)
            except SectionError as error:
                raise AssertionError(f"{core.path}: {error}") from error


def test_spec_map_code_paths_exist():
    for core in _SPEC_MAP.core_docs:
        for code in core.code:
            assert not Path(code).is_absolute(), code
            assert (_REPO_ROOT / code).exists(), f"{core.path}: code path {code} does not exist"


def test_spec_map_core_defs_exist_in_the_vendored_schema():
    defs = _load_schema()["$defs"]
    assert len(set(_SPEC_MAP.core_defs)) == len(_SPEC_MAP.core_defs)
    assert not [name for name in _SPEC_MAP.core_defs if name not in defs]
    assert set(_SPEC_MAP.core_defs) >= {
        "ErrorCode",
        "SessionUpdate",
        "ContentBlock",
        "AgentCapabilities",
        "ClientCapabilities",
    }


def test_spec_map_ledger_citations_resolve_like_requirement_citations():
    schema = _load_schema()
    for entry in _SPEC_MAP.not_requirements:
        assert not _ledger_citation_problems(entry.citation, schema), entry.citation


def test_spec_map_ledger_check_accepts_a_good_entry_and_flags_bad_ones():
    def entry(citation: str):
        (parsed,) = parse_spec_map(
            "core_defs = []\n[[not_requirement]]\n"
            f"citation = {json.dumps(citation)}\nstatement = \"s\"\nreason = \"r\"\n"
        ).not_requirements
        return parsed.citation

    schema = _load_schema()
    good = (
        "docs/protocol/v1/draft/transports.mdx:6; "
        f"schema/v1/schema.unstable.json#/$defs/ErrorCode @ {SCHEMA_REVISION}"
    )
    assert _ledger_citation_problems(entry(good), schema) == []
    assert _ledger_citation_problems(entry("docs/protocol/v1/draft/transports.mdx:6"), schema)
    assert _ledger_citation_problems(entry(f"x.mdx @ {'0' * 40}"), schema)
    assert _ledger_citation_problems(
        entry(f"schema.unstable.json#/$defs/NoSuchDef @ {SCHEMA_REVISION}"), schema
    )
    assert _ledger_citation_problems(entry(f"schema/v1/schema.json @ {SCHEMA_REVISION}"), schema)
    assert _ledger_citation_problems(entry(f"docs/protocol/v1/session-setup.mdx:1 @ {SCHEMA_REVISION}"), schema)
