"""`spec_tracker.citations`: parsing the machine-readable parts of registry and ledger citations."""

from __future__ import annotations

import pytest

from spec_tracker.citations import LineRef, find_line_refs, line_refs, pointer_def, resolve_pointer, schema_pointers


def test_resolve_pointer_handles_escapes_and_arrays():
    doc = {"a/b": {"c~d": [10, {"x": 1}]}}
    assert resolve_pointer(doc, "/a~1b/c~0d/1/x") == 1
    assert resolve_pointer(doc, "") is doc
    for bad in ("/a~1b/c~0d/2", "/a~1b/c~0d/01", "/a/b", "/a~1b/c~0d/x"):
        with pytest.raises((KeyError, IndexError, ValueError)):
            resolve_pointer(doc, bad)


def test_schema_pointers_keep_own_version_and_bare_file_only():
    text = (
        "schema/v1/schema.unstable.json#/$defs/A; schema/v2/schema.unstable.json#/$defs/B; "
        "schema.unstable.json#/$defs/C/properties/x. (note)"
    )
    assert schema_pointers(text, "v1") == ["/$defs/A", "/$defs/C/properties/x"]
    assert schema_pointers(text, "v2") == ["/$defs/B", "/$defs/C/properties/x"]


def test_pointer_def():
    assert pointer_def("/$defs/StopReason") == "StopReason"
    assert pointer_def("/$defs/IdleStateUpdate/anyOf/4") == "IdleStateUpdate"
    assert pointer_def("/$defs/a~1b") == "a/b"
    assert pointer_def("/anyOf/2") is None
    assert pointer_def("") is None


def test_line_refs_parse_paths_and_ranges():
    citation = (
        "docs/protocol/v1/draft/initialization.mdx:247, docs/protocol/v1/draft/content.mdx:31 "
        "(Req 7); docs/protocol/v1/draft/prompt-turn.mdx:578-590,598; "
        "docs/protocol/v2/draft/error.mdx; schema/v2/meta.unstable.json:31-37 (inventory); "
        "docs/rfds/v2/prompt.mdx:88 @ " + "0" * 40
    )
    assert line_refs(citation) == [
        LineRef("docs/protocol/v1/draft/initialization.mdx", ((247, 247),)),
        LineRef("docs/protocol/v1/draft/content.mdx", ((31, 31),)),
        LineRef("docs/protocol/v1/draft/prompt-turn.mdx", ((578, 590), (598, 598))),
        LineRef("docs/protocol/v2/draft/error.mdx", ()),
        LineRef("schema/v2/meta.unstable.json", ((31, 37),)),
        LineRef("docs/rfds/v2/prompt.mdx", ((88, 88),)),
    ]


def test_line_refs_skip_schema_pointers_and_non_spec_paths():
    citation = (
        "schema/v1/schema.unstable.json#/$defs/StopReason; "
        "agent-client-protocol-schema/src/v1/error.rs:40-42; "
        "rust-sdk@d5e8bf4 src/agent-client-protocol/tests/x.rs:1"
    )
    assert line_refs(citation) == []


def test_find_line_refs_locates_each_line_spec():
    text = "see docs/a.mdx:5-7,9 and docs/b.mdx; schema/v1/schema.unstable.json#/$defs/X"
    matches = find_line_refs(text)
    assert [m.ref.path for m in matches] == ["docs/a.mdx", "docs/b.mdx"]
    first, second = matches
    assert first.spec_span is not None and text[slice(*first.spec_span)] == "5-7,9"
    assert second.spec_span is None
