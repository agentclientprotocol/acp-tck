"""Checks of `maps/v2.toml` (the v2 spec map) against the spec docs at the pinned revision, the
vendored schema, and the product code it points at. Doc-reading tests need the spec checkout (see
`conftest.spec_doc`)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from spec_tracker.citations import resolve_pointer, schema_pointers
from spec_tracker.spec_map import SectionError, load_version_map, parse_spec_map, resolve_section
from tck.v2.protocol import SCHEMA_DIR, SCHEMA_REVISION

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SPEC_REVISION_PATTERN = re.compile(r"@ [0-9a-f]{40}$")
# Any mention of the stable file names; `schema.unstable.json` does not match.
_STABLE_NAME_PATTERN = re.compile(r"\b(?:schema|meta)\.json\b")
# Prose citations point at the draft doc tree, matching the draft schema.
_NON_DRAFT_DOCS_PATTERN = re.compile(r"docs/protocol/v2/(?!draft/)")

_SPEC_MAP = load_version_map("v2")
_DOC_PATH_PATTERN = re.compile(r"^docs/protocol/v2/draft/[a-z0-9-]+\.mdx$")


def _unresolved_pointers(pointers_by_source: dict[str, list[str]], schema: Any) -> list[str]:
    bad = []
    for source, pointers in pointers_by_source.items():
        for pointer in pointers:
            try:
                resolve_pointer(schema, pointer)
            except (KeyError, IndexError, ValueError):
                bad.append(f"{source}: {pointer}")
    return bad


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
        for pointer in _unresolved_pointers({"c": schema_pointers(citation, "v2")}, schema)
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


def test_spec_map_prompt_lifecycle_covers_everything_but_the_standalone_features(spec_doc):
    core = next(c for c in _SPEC_MAP.core_docs if c.path.endswith("/prompt-lifecycle.mdx"))
    text = spec_doc(SCHEMA_REVISION, core.path)
    covered = set()
    for section in core.sections:
        start, end = resolve_section(text, section)
        covered.update(range(start, end + 1))
    left_out = set()
    for title in (
        "Session-directed messages (unstable)",
        "Session Notices",
        "Session Compaction",
        "Session Usage Updates",
        "End-Turn Token Usage (Unstable)",
    ):
        start, end = resolve_section(text, title)
        left_out.update(range(start, end + 1))
    assert not covered & left_out
    assert covered | left_out == set(range(1, len(text.splitlines()) + 1))


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
        "docs/protocol/v2/draft/transports.mdx:6; "
        f"schema/v2/schema.unstable.json#/$defs/ErrorCode @ {SCHEMA_REVISION}"
    )
    assert _ledger_citation_problems(entry(good), schema) == []
    assert _ledger_citation_problems(entry("docs/protocol/v2/draft/transports.mdx:6"), schema)
    assert _ledger_citation_problems(entry(f"x.mdx @ {'0' * 40}"), schema)
    assert _ledger_citation_problems(
        entry(f"schema.unstable.json#/$defs/NoSuchDef @ {SCHEMA_REVISION}"), schema
    )
    assert _ledger_citation_problems(entry(f"schema/v2/schema.json @ {SCHEMA_REVISION}"), schema)
    assert _ledger_citation_problems(entry(f"docs/protocol/v2/session-setup.mdx:1 @ {SCHEMA_REVISION}"), schema)
