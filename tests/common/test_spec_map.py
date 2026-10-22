"""Unit tests for `tck.common.spec_map`: the TOML parser's shape checks and the heading scanner."""

from __future__ import annotations

import pytest

from tck.common.spec_map import (
    SectionError,
    SpecMapError,
    markdown_headings,
    parse_spec_map,
    resolve_section,
)

_MINIMAL = 'core_defs = ["ErrorCode"]\n'


def test_parses_core_docs_defs_and_ledger():
    spec_map = parse_spec_map(
        _MINIMAL
        + """
[[core_doc]]
path = "docs/protocol/v1/draft/a.mdx"
sections = ["One", "Two"]
code = ["src/x.py"]
reason = "why"

[[core_doc]]
path = "docs/protocol/v1/draft/b.mdx"
reason = "whole doc"

[[not_requirement]]
citation = "c @ abc"
statement = "s"
reason = "r"
"""
    )
    assert spec_map.core_defs == ("ErrorCode",)
    first, second = spec_map.core_docs
    assert (first.path, first.sections, first.code, first.reason) == (
        "docs/protocol/v1/draft/a.mdx",
        ("One", "Two"),
        ("src/x.py",),
        "why",
    )
    assert second.sections == () and second.code == ()
    (entry,) = spec_map.not_requirements
    assert (entry.citation, entry.statement, entry.reason) == ("c @ abc", "s", "r")


def test_empty_ledger_is_allowed():
    assert parse_spec_map(_MINIMAL).not_requirements == ()


@pytest.mark.parametrize(
    "extra, message",
    [
        ('[[core_doc]]\npath = "p"\n', "'reason'"),
        ('[[core_doc]]\nreason = "r"\n', "'path'"),
        ('[[core_doc]]\npath = "p"\nreason = "r"\nsections = "One"\n', "'sections'"),
        ('[[core_doc]]\npath = "p"\nreason = "r"\ncodes = []\n', "unknown key"),
        ('[[not_requirement]]\ncitation = "c"\nstatement = "s"\n', "'reason'"),
        ('[[not_requirement]]\ncitation = "c"\nstatement = " "\nreason = "r"\n', "'statement'"),
        ('[[not_requirement]]\ncitation = "c"\nstatement = "s"\nreason = "r"\nextra = 1\n', "unknown key"),
        ("[[stray]]\n", "unknown key"),
    ],
)
def test_malformed_entries_are_rejected(extra, message):
    with pytest.raises(SpecMapError, match=message):
        parse_spec_map(_MINIMAL + extra)


def test_core_defs_is_required():
    with pytest.raises(SpecMapError, match="core_defs"):
        parse_spec_map("")
    # An empty list is still a list of strings, so a map with no core defs is valid.
    assert parse_spec_map("core_defs = []").core_defs == ()


def test_markdown_headings_ignores_code_fences_and_trailing_hashes():
    text = (
        "# Title\n"
        "intro\n"
        "## The `_meta` Field\n"
        "```bash\n"
        "# not a heading\n"
        "```\n"
        "### Sub ###\n"
        "#no-space is not a heading\n"
        "~~~\n"
        "## also fenced\n"
        "~~~\n"
        "#### Last\n"
    )
    assert markdown_headings(text) == ["Title", "The `_meta` Field", "Sub", "Last"]


_DOC = """\
---
title: "Doc"
---

Doc intro.

## Agent
Agent own text.
### Baseline Methods
agent baseline
### Notifications
agent notes
## Client
Client own text.
### Baseline Methods
client baseline
```bash
# not a heading
## nor this
```
tail of client baseline
### Optional Methods
optional
## Last
"""


def _lines(address):
    start, end = resolve_section(_DOC, address)
    return _DOC.splitlines()[start - 1 : end]


def test_plain_title_covers_its_subsections():
    lines = _lines("Client")
    assert lines[0] == "## Client"
    assert lines[-1] == "optional"
    assert "client baseline" in lines and "## Agent" not in lines and "## Last" not in lines


def test_path_picks_one_of_two_duplicate_titles():
    assert _lines("Agent > Baseline Methods") == ["### Baseline Methods", "agent baseline"]
    client = _lines("Client > Baseline Methods")
    assert client[1] == "client baseline"
    # Code-fence `#` lines belong to the section, they do not end it.
    assert client[-1] == "tail of client baseline"


def test_duplicate_title_without_path_is_ambiguous():
    with pytest.raises(SectionError, match="ambiguous"):
        resolve_section(_DOC, "Baseline Methods")


@pytest.mark.parametrize(
    "address",
    [
        "Missing",
        "Agent > Optional Methods",  # exists, but under Client
        "Baseline Methods > Agent",  # parents run top-down
        "Client > Baseline Methods > Deeper",
        "not a heading",  # only appears inside a code fence
        "nor this",
    ],
)
def test_missing_titles_and_paths_are_rejected(address):
    with pytest.raises(SectionError, match="no heading"):
        resolve_section(_DOC, address)


def test_path_requires_direct_children():
    doc = "# A\n## B\n### C\n"
    assert resolve_section(doc, "A > B > C") == (3, 3)
    with pytest.raises(SectionError, match="no heading"):
        resolve_section(doc, "A > C")


def test_doc_level_intro_is_the_text_before_the_first_heading():
    start, end = resolve_section(_DOC, "(intro)")
    assert (start, end) == (1, _DOC.splitlines().index("## Agent"))
    assert "Doc intro." in _DOC.splitlines()[start - 1 : end]


def test_doc_level_intro_of_a_doc_that_starts_with_a_heading_is_rejected():
    with pytest.raises(SectionError, match="no text before"):
        resolve_section("# Title\ntext\n", "(intro)")


def test_heading_intro_stops_at_the_first_child_heading():
    assert _lines("Agent > (intro)") == ["## Agent", "Agent own text."]
    assert _lines("Client > (intro)") == ["## Client", "Client own text."]
    assert _lines("Client > Baseline Methods > (intro)") == [
        "### Baseline Methods",
        "client baseline",
        "```bash",
        "# not a heading",
        "## nor this",
        "```",
        "tail of client baseline",
    ]


def test_intro_of_a_heading_without_children_is_the_whole_section():
    assert _lines("Last > (intro)") == _lines("Last") == ["## Last"]


def test_intro_marker_is_only_valid_last():
    with pytest.raises(SectionError, match="only valid as the last"):
        resolve_section(_DOC, "(intro) > Agent")


@pytest.mark.parametrize("address", ["", "Agent > ", " > Agent"])
def test_empty_address_parts_are_rejected(address):
    with pytest.raises(SectionError, match="empty title"):
        resolve_section(_DOC, address)


def test_frontmatter_hashes_are_not_headings():
    doc = "---\n# comment\ntitle: x\n---\ntext\n# Real\n"
    assert markdown_headings(doc) == ["Real"]


def test_intro_and_sections_tile_a_doc_exactly():
    """An inclusion list of `(intro)` plus intros and leaves covers every line once."""
    ranges = [resolve_section(_DOC, a) for a in ("(intro)", "Agent", "Client", "Last")]
    covered = [n for start, end in ranges for n in range(start, end + 1)]
    assert covered == list(range(1, len(_DOC.splitlines()) + 1))
