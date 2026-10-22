"""`scripts/spec-impact.py`: unit tests for its building blocks, plus a full report over a small
synthetic spec repo with two commits.

`scripts/` is not a package, so the module is loaded from its file path (as in
`test_cross_check_summary.py`).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tck.common.spec_map import Heading, parse_spec_map

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "spec-impact.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("spec_impact", _SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(module)
    return module


si = _load_module()
Hunk = si.Hunk


# --- diff parsing ----------------------------------------------------------------------------


def test_parse_diff_reads_hunks_per_file_including_deletions_and_omitted_counts():
    text = "\n".join(
        [
            "diff --git a/docs/a.mdx b/docs/a.mdx",
            "index 1..2 100644",
            "--- a/docs/a.mdx",
            "+++ b/docs/a.mdx",
            "@@ -3 +3 @@ ## Heading",
            "-old",
            "+new",
            "@@ -10,0 +11,2 @@",
            "+x",
            "+y",
            "\\ No newline at end of file",
            "diff --git a/docs/gone.mdx b/docs/gone.mdx",
            "deleted file mode 100644",
            "--- a/docs/gone.mdx",
            "+++ /dev/null",
            "@@ -1,2 +0,0 @@",
            "-a",
            "-b",
            "diff --git a/img.png b/img.png",
            "Binary files a/img.png and b/img.png differ",
        ]
    )
    assert si.parse_diff(text) == {
        "docs/a.mdx": [Hunk(3, 1, 3, 1), Hunk(10, 0, 11, 2)],
        "docs/gone.mdx": [Hunk(1, 2, 0, 0)],
    }


def test_hunk_line_ranges_follow_gits_zero_count_convention():
    insertion = Hunk(10, 0, 11, 2)
    assert list(insertion.old_lines) == [] and list(insertion.new_lines) == [11, 12]
    assert si.hunk_side(insertion) == "target"
    assert si.hunk_side(Hunk(3, 1, 3, 0)) == "base"
    assert insertion.label() == "-10,0 +11,2"


@pytest.mark.parametrize(
    ("hunk", "start", "end", "touched"),
    [
        (Hunk(5, 2, 5, 1), 6, 9, True),  # replaces line 6
        (Hunk(5, 2, 5, 1), 7, 9, False),
        (Hunk(5, 2, 5, 1), 1, 5, True),
        (Hunk(5, 0, 6, 3), 3, 8, True),  # insertion after line 5, inside 3-8
        (Hunk(5, 0, 6, 3), 5, 5, False),  # insertion right after the cited line
        (Hunk(5, 0, 6, 3), 6, 9, False),  # insertion right before the cited range
        (Hunk(5, 0, 6, 3), 5, 6, True),
    ],
)
def test_hunk_touches_base_range(hunk, start, end, touched):
    assert si.hunk_touches_base_range(hunk, start, end) is touched


# --- sections --------------------------------------------------------------------------------


def test_heading_path_at_walks_nesting_and_strips_html():
    headings = [
        Heading("Top", 1, 3),
        Heading("A", 2, 5),
        Heading('<span class="font-mono">x/y</span>', 3, 7),
        Heading("B", 2, 10),
    ]
    assert si.heading_path_at(headings, 1) == "(intro)"
    assert si.heading_path_at(headings, 3) == "Top"
    assert si.heading_path_at(headings, 8) == "Top > A > x/y"
    assert si.heading_path_at(headings, 10) == "Top > B"
    assert si.heading_path_at([], 4) == "(intro)"


def test_hunk_sections_use_base_for_changes_and_target_for_additions():
    base = "# T\n\n## A\n\na\n\n## B\n\nb\n"
    target = "# T\n\n## A\n\na\n\n## B\n\nb\nmore\n"
    assert si.hunk_sections(Hunk(5, 5, 5, 1), base, target) == ["T > A", "T > B"]
    assert si.hunk_sections(Hunk(9, 0, 10, 1), base, target) == ["T > B"]


def test_slugify():
    assert si.slugify("3. Agent Reports Output") == "3-agent-reports-output"
    assert si.slugify("Session-directed messages (unstable)") == "session-directed-messages-unstable"
    assert si.slugify('<span class="font-mono">session/request_permission</span>') == "session/request_permission"


# --- schema ----------------------------------------------------------------------------------


def test_refs_in_collects_local_def_refs_only():
    node = {"anyOf": [{"$ref": "#/$defs/A"}, {"items": {"$ref": "#/$defs/B/properties/c"}}], "x": {"$ref": "other.json"}}
    assert si.refs_in(node) == {"A", "B"}


def test_ref_closure_follows_chains_cycles_and_both_revisions():
    base = {"A": {"$ref": "#/$defs/B"}, "B": {"$ref": "#/$defs/C"}, "C": {}, "D": {"$ref": "#/$defs/D"}, "E": {"$ref": "#/$defs/C"}}
    target = {"A": {"$ref": "#/$defs/B"}, "B": {"$ref": "#/$defs/C"}, "C": {}, "D": {}, "F": {"$ref": "#/$defs/B"}}
    # E references C only at base, F only at target; both count.
    assert si.ref_closure({"C"}, base, target) == {"A": {"C"}, "B": {"C"}, "E": {"C"}, "F": {"C"}}
    # Directly changed defs are not repeated in the closure.
    assert si.ref_closure({"B", "C"}, base, target) == {"A": {"B", "C"}, "E": {"C"}, "F": {"B", "C"}}


def test_diff_defs_and_root_pseudo_def():
    base = si.schema_nodes({"anyOf": [1], "$defs": {"A": {"x": 1}, "B": {}, "Gone": {}}})
    target = si.schema_nodes({"anyOf": [2], "$defs": {"A": {"x": 1}, "B": {"y": 1}, "New": {}}})
    defs = si.diff_defs(base, target)
    assert (defs.added, defs.removed, defs.changed) == (("New",), ("Gone",), ("(root)", "B"))
    assert si.schema_nodes(None) == {}


# --- links -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("/protocol/v1/prompt-turn#cancellation", ("docs/protocol/v1/draft/prompt-turn.mdx", "cancellation")),
        ("/protocol/v1/draft/schema#session%2Fnew", ("docs/protocol/v1/draft/schema.mdx", "session%2Fnew")),
        ("https://agentclientprotocol.com/protocol/v2/draft/extensibility", ("docs/protocol/v2/draft/extensibility.mdx", None)),
        ("/rfds/subagents#x", ("docs/rfds/subagents.mdx", "x")),
        ("./content", ("docs/protocol/v1/draft/content.mdx", None)),
        ("content.mdx", ("docs/protocol/v1/draft/content.mdx", None)),
        ("../initialization", ("docs/protocol/v1/draft/initialization.mdx", None)),
        ("#local", ("docs/protocol/v1/draft/here.mdx", "local")),
        ("https://www.jsonrpc.org/specification", None),
        ("mailto:a@b.c", None),
    ],
)
def test_normalize_link(url, expected):
    assert si.normalize_link(url, "docs/protocol/v1/draft/here.mdx") == expected


def test_doc_links_skip_code_fences():
    text = "[a](/x)\n```\n[b](/y)\n```\n<Card href=\"/z\" /> [c](/w \"title\")\n"
    assert si.doc_links(text) == [(1, "/x"), (5, "/w"), (5, "/z")]


# --- synthetic spec repo ---------------------------------------------------------------------

_GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"]
D = "docs/protocol/v1/draft"
SCHEMA = "schema/v1/schema.unstable.json"

CORE_BASE = """---
title: Core
---

Intro text.

## Alpha

alpha line

### Alpha Sub

sub line

## Beta

beta line

## Gamma

gamma line
"""
# Inserts a line after base line 13 (`-13,0 +14,1`) and rewrites base line 17 (`-17,1 +18,1`).
CORE_TARGET = CORE_BASE.replace("sub line\n", "sub line\nnew sub line\n").replace("beta line", "beta line, changed")

FEATURE = """# Feature

See [beta](/protocol/v1/core#beta) and [alpha](https://agentclientprotocol.com/protocol/v1/draft/core#alpha).
Also [core](./core), [gamma](../draft/core.mdx#gamma), [thing](/rfds/thing), [ext](https://example.com/x).
<Card href="/protocol/v1/draft/gone">gone</Card>
[self](#feature)
```
[in fence](/protocol/v1/draft/core)
```
[bogus](/protocol/v1/draft/core#nope)
"""

SCHEMA_BASE = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "anyOf": [{"$ref": "#/$defs/Req"}],
    "$defs": {
        "Req": {"properties": {"params": {"$ref": "#/$defs/Params"}}},
        "Params": {"anyOf": [{"$ref": "#/$defs/Leaf"}, {"$ref": "#/$defs/Params"}]},
        "Leaf": {"type": "string"},
        "Other": {"type": "integer"},
        "Cyc1": {"$ref": "#/$defs/Cyc2"},
        "Cyc2": {"$ref": "#/$defs/Cyc1"},
        "Removed": {"type": "null"},
    },
}
SCHEMA_TARGET = json.loads(json.dumps(SCHEMA_BASE))
SCHEMA_TARGET["$defs"]["Leaf"]["description"] = "now documented"
del SCHEMA_TARGET["$defs"]["Removed"]
SCHEMA_TARGET["$defs"]["Added"] = {"type": "boolean"}

SPEC_MAP = parse_spec_map(
    f"""
core_defs = ["Req", "Leaf", "Other"]

[[core_doc]]
path = "{D}/core.mdx"
sections = ["(intro)", "Alpha > Alpha Sub", "Beta", "Delta"]
code = ["src/x.py"]
reason = "r"

[[core_doc]]
path = "{D}/feature.mdx"
reason = "unchanged"

[[core_doc]]
path = "{D}/gone.mdx"
code = ["src/gone.py"]
reason = "removed"
"""
)

ENTRIES = [
    ("REQ-BETA", f"{D}/core.mdx:15-17 @ x"),
    ("REQ-INTRO", f"{D}/core.mdx:5 @ x"),
    ("REQ-SUB-EDGE", f"{D}/core.mdx:13 @ x"),
    ("REQ-SUB-RANGE", f"{D}/core.mdx:11-14 @ x"),
    ("REQ-PARAMS", f"{SCHEMA}#/$defs/Params/anyOf/0 @ x"),
    ("REQ-LEAF", f"{SCHEMA}#/$defs/Leaf @ x"),
    ("REQ-OTHER", f"{SCHEMA}#/$defs/Other; schema/v2/schema.unstable.json#/$defs/Leaf @ x"),
    ("REQ-ROOT", f"{SCHEMA}#/anyOf/0 @ x"),
    ("REQ-RFD", "docs/rfds/thing.mdx:3 @ x"),
    ("REQ-GONE", f"{D}/gone.mdx:1 @ x"),
    ("REQ-WHOLE", f"{D}/core.mdx @ x"),
    ("ledger `s`", f"{D}/core.mdx:17 @ x"),
]


def _write(repo: Path, files: dict[str, str | None]) -> str:
    for path, content in files.items():
        target = repo / path
        if content is None:
            target.unlink()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    subprocess.run([*_GIT, "-C", str(repo), "add", "-A"], check=True)
    subprocess.run([*_GIT, "-C", str(repo), "commit", "-q", "-m", "c"], check=True)
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture(scope="module")
def spec_repo(tmp_path_factory) -> tuple[Path, str, str]:
    repo = tmp_path_factory.mktemp("spec")
    subprocess.run([*_GIT, "-C", str(repo), "init", "-q"], check=True)
    base = _write(
        repo,
        {
            f"{D}/core.mdx": CORE_BASE,
            f"{D}/feature.mdx": FEATURE,
            f"{D}/gone.mdx": "# Gone\n\ntext\n",
            "docs/protocol/v1/core.mdx": "# stable copy, out of scope\n",
            "docs/rfds/thing.mdx": "# Thing\n\nline three\n\nline five\n",
            SCHEMA: json.dumps(SCHEMA_BASE, indent=2),
        },
    )
    target = _write(
        repo,
        {
            f"{D}/core.mdx": CORE_TARGET,
            f"{D}/gone.mdx": None,
            f"{D}/new.mdx": "# New\n\nnew text\n",
            "docs/protocol/v1/core.mdx": "# stable copy, changed\n",
            "docs/rfds/thing.mdx": "# Thing\n\nline three\n\nline five, changed\n",
            SCHEMA: json.dumps(SCHEMA_TARGET, indent=2),
        },
    )
    return repo, base, target


@pytest.fixture(scope="module")
def report(spec_repo):
    repo, base, target = spec_repo
    return si.analyze(si.SpecRepo(repo), base, target, "v1", SPEC_MAP, ENTRIES)


def test_changed_files_are_scoped_to_the_versions_draft_tree_schema_and_rfds(report):
    assert {path: change.status for path, change in report.changes.items()} == {
        f"{D}/core.mdx": "M",
        f"{D}/gone.mdx": "D",
        f"{D}/new.mdx": "A",
        "docs/rfds/thing.mdx": "M",
        SCHEMA: "M",
    }
    assert report.changes[f"{D}/core.mdx"].hunks == (Hunk(13, 0, 14, 1), Hunk(17, 1, 18, 1))


def test_doc_hunks_map_to_sections(report):
    assert report.sections[f"{D}/core.mdx"] == [
        (Hunk(13, 0, 14, 1), ["Alpha > Alpha Sub"]),
        (Hunk(17, 1, 18, 1), ["Beta"]),
    ]
    assert report.sections[f"{D}/gone.mdx"] == [(Hunk(1, 3, 0, 0), ["Gone"])]
    assert report.sections[f"{D}/new.mdx"] == [(Hunk(0, 0, 1, 3), ["New"])]
    assert "docs/rfds/thing.mdx" not in report.sections


def test_core_hits(report):
    hits = {(hit.core.path, hit.section): hit.hunks for hit in report.core}
    assert hits == {
        (f"{D}/core.mdx", "Alpha > Alpha Sub"): (Hunk(13, 0, 14, 1),),
        (f"{D}/core.mdx", "Beta"): (Hunk(17, 1, 18, 1),),
        (f"{D}/gone.mdx", None): (Hunk(1, 3, 0, 0),),
    }
    assert len(report.core_notes) == 2
    assert all("`Delta`" in note for note in report.core_notes)


def test_schema_changes_closure_and_core_defs(report):
    defs = report.schema.defs
    assert (defs.added, defs.removed, defs.changed) == (("Added",), ("Removed",), ("Leaf",))
    assert report.schema.closure == {"Params": {"Leaf"}, "Req": {"Leaf"}, "(root)": {"Leaf"}}
    assert report.core_defs == [("Req", "via $ref closure of `Leaf`"), ("Leaf", "changed directly")]


def test_link_fan_out(report):
    def links(path):
        return [(h.source, h.line, h.anchor, h.anchor_status) for h in report.fan_out[path]]

    feature = f"{D}/feature.mdx"
    assert links(f"{D}/core.mdx") == [
        (feature, 3, "beta", "changed section"),
        (feature, 3, "alpha", "changed section"),
        (feature, 4, None, None),
        (feature, 4, "gamma", "unchanged section"),
        (feature, 10, "nope", "unknown anchor"),
    ]
    assert links(f"{D}/gone.mdx") == [(feature, 5, None, None)]
    assert links("docs/rfds/thing.mdx") == [(feature, 4, None, None)]
    assert links(f"{D}/new.mdx") == []


def test_affected_entries(report):
    affected = dict(report.affected)
    assert set(affected) == {
        "REQ-BETA",
        "REQ-SUB-RANGE",
        "REQ-PARAMS",
        "REQ-LEAF",
        "REQ-ROOT",
        "REQ-RFD",
        "REQ-GONE",
        "REQ-WHOLE",
        "ledger `s`",
    }
    assert affected["REQ-BETA"] == [f"`{D}/core.mdx:15-17` overlaps hunk `-17,1 +18,1`"]
    assert affected["REQ-SUB-RANGE"] == [f"`{D}/core.mdx:11-14` overlaps hunk `-13,0 +14,1`"]
    assert affected["REQ-PARAMS"] == ["`#/$defs/Params/anyOf/0`: `Params` in $ref closure of `Leaf`"]
    assert affected["REQ-LEAF"] == ["`#/$defs/Leaf`: `Leaf` changed"]
    assert affected["REQ-ROOT"] == ["`#/anyOf/0`: `(root)` in $ref closure of `Leaf`"]
    assert affected["REQ-RFD"] == ["cites changed RFD `docs/rfds/thing.mdx` (cited lines untouched)"]
    assert affected["REQ-GONE"] == [f"cites `{D}/gone.mdx`, which was removed"]
    assert affected["REQ-WHOLE"] == [f"cites all of `{D}/core.mdx`, which changed"]


def test_rendered_report_has_every_section_and_an_escalating_summary(report):
    text = si.render(report)
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    assert headings == [
        "## 1. Changed files",
        "## 2. Doc hunks -> sections",
        "## 3. Core hits",
        "## 4. Schema",
        "## 5. Link fan-out",
        "## 6. Affected entries",
        "## Summary",
    ]
    assert f"- `{D}/core.mdx` (section `Beta`): `-17,1 +18,1`; code: `src/x.py`" in text
    assert f"- `{D}/gone.mdx` (whole doc): `-1,3 +0,0`; code: `src/gone.py`" in text
    assert "  - `Params` -> `Leaf`" in text
    assert f"- `{D}/feature.mdx:3` `#beta` (changed section)" in text
    assert "- Affected entries: 8 requirements, 1 ledger entries." in text
    assert "- Core hit: **yes, escalate**" in text


def test_no_change_report_does_not_escalate(spec_repo):
    repo, _, target = spec_repo
    report = si.analyze(si.SpecRepo(repo), target, target, "v1", SPEC_MAP, ENTRIES)
    assert not report.changes and not report.affected and not report.escalate
    text = si.render(report)
    assert "- Core hit: no" in text and "No core doc or section touched." in text


def test_cli_runs_read_only_against_a_spec_repo(spec_repo):
    repo, base, _ = spec_repo
    before = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout
    result = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), base, "HEAD", "--version", "v1", "--spec-repo", str(repo)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(f"# Spec impact (v1): `{base[:12]}` -> ")
    assert f"- removed: `{D}/gone.mdx`" in result.stdout
    after = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout
    assert before == after == ""


def test_cli_rejects_an_unknown_revision(spec_repo):
    repo, base, _ = spec_repo
    result = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), base, "0" * 40, "--version", "v1", "--spec-repo", str(repo)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "cannot resolve revision" in result.stderr


# --- citation remapping (--fix) --------------------------------------------------------------


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (5, 5, (5, 5)),  # above every hunk
        (13, 13, (13, 13)),  # right before the insertion after line 13
        (14, 15, (15, 16)),  # below the insertion
        (11, 14, None),  # insertion strictly inside the range
        (17, 17, None),  # replaced line
        (16, 18, None),
        (19, 22, (20, 23)),  # below both hunks: +1 and +0
    ],
)
def test_remap_range_shifts_by_the_hunks_above_and_refuses_changed_ranges(start, end, expected):
    hunks = [Hunk(13, 0, 14, 1), Hunk(17, 1, 18, 1)]
    mapped, touching = si.remap_range(hunks, start, end)
    assert mapped == expected
    assert bool(touching) is (expected is None)


def test_remap_range_after_a_pure_deletion_shifts_up():
    assert si.remap_range([Hunk(3, 2, 2, 0)], 6, 8) == ((4, 6), [])
    assert si.remap_range([Hunk(3, 2, 2, 0)], 4, 4)[0] is None


def test_remap_citation_keeps_shape_and_leaves_unmappable_elements(spec_repo):
    repo, base, target = spec_repo
    changes = si.file_changes(si.SpecRepo(repo), base, target, "v1")
    text = (
        f"{D}/core.mdx:5,15,17,19-20; {D}/core.mdx:15-17; {D}/core.mdx:21 @ x; "
        f"{D}/gone.mdx:1; docs/rfds/thing.mdx:3,5; {SCHEMA}:2-3; {D}/new.mdx:1; {D}/untouched.mdx:9; "
        f"{D}/core.mdx; agent-client-protocol-schema/src/rpc.rs:14-16"
    )
    new, results = si.remap_citation(text, changes)
    assert new == (
        f"{D}/core.mdx:5,16,17,20-21; {D}/core.mdx:15-17; {D}/core.mdx:22 @ x; "
        f"{D}/gone.mdx:1; docs/rfds/thing.mdx:3,5; {SCHEMA}:2-3; {D}/new.mdx:1; {D}/untouched.mdx:9; "
        f"{D}/core.mdx; agent-client-protocol-schema/src/rpc.rs:14-16"
    )
    assert [(r.old, r.new, r.why) for r in results] == [
        (f"{D}/core.mdx:15", f"{D}/core.mdx:16", ""),
        (f"{D}/core.mdx:17", None, "overlaps hunk `-17,1 +18,1`"),
        (f"{D}/core.mdx:19-20", f"{D}/core.mdx:20-21", ""),
        (f"{D}/core.mdx:15-17", None, "overlaps hunk `-17,1 +18,1`"),
        (f"{D}/core.mdx:21", f"{D}/core.mdx:22", ""),
        (f"{D}/gone.mdx:1", None, "file removed"),
        ("docs/rfds/thing.mdx:5", None, "overlaps hunk `-5,1 +5,1`"),
        (f"{SCHEMA}:2-3", None, "line citations into a non-doc file are not remapped"),
    ]


_REQUIREMENTS_SOURCE = f'''\
SPEC_REVISION = "abc"
_cite = make_cite(SPEC_REVISION)

_DECLARATIONS = (
    Requirement(
        id="REQ-A",
        text="Mentions {D}/core.mdx:15 in prose, which is not a citation.",
        citation=_cite("{D}/core.mdx:15,19"),
    ),
    Requirement(
        id="REQ-B",
        text="café — unicode before the citation",
        citation=_cite(
            "{D}/core.mdx:15-17; "
            "agent-client-protocol-schema/src/rpc.rs:14-16; "
            "{D}/core.mdx:18-19, {D}/core.mdx:5 — é"
            "; {SCHEMA}#/$defs/Leaf"
        ),
    ),
)
'''

_SPEC_MAP_SOURCE = f'''\
# Ledger mentions {D}/core.mdx:15 in a comment.
core_defs = []

[[not_requirement]]
citation = "{D}/core.mdx:15-16 @ abc"
statement = "first"
reason = "r"

[[not_requirement]]
citation = "{D}/core.mdx:17,19 @ abc"
statement = "second"
reason = "r"
'''


def test_apply_fix_edits_text_in_place_and_reports_each_entry(spec_repo, tmp_path):
    repo, base, target = spec_repo
    changes = si.file_changes(si.SpecRepo(repo), base, target, "v1")
    requirements, spec_map = tmp_path / "requirements.py", tmp_path / "spec_map.toml"
    requirements.write_text(_REQUIREMENTS_SOURCE)
    spec_map.write_text(_SPEC_MAP_SOURCE)

    result = si.apply_fix(requirements, spec_map, changes)

    assert requirements.read_text() == (
        _REQUIREMENTS_SOURCE.replace(f"citation=_cite(\"{D}/core.mdx:15,19\")", f"citation=_cite(\"{D}/core.mdx:16,20\")")
        .replace(f"{D}/core.mdx:18-19, {D}/core.mdx:5", f"{D}/core.mdx:19-20, {D}/core.mdx:5")
    )
    assert spec_map.read_text() == _SPEC_MAP_SOURCE.replace("core.mdx:15-16 @", "core.mdx:16-17 @").replace(
        "core.mdx:17,19 @", "core.mdx:17,20 @"
    )
    assert [(label, r.old, r.new) for label, r in result.rewritten] == [
        ("REQ-A", f"{D}/core.mdx:15", f"{D}/core.mdx:16"),
        ("REQ-A", f"{D}/core.mdx:19", f"{D}/core.mdx:20"),
        ("REQ-B", f"{D}/core.mdx:18-19", f"{D}/core.mdx:19-20"),
        ("ledger `first`", f"{D}/core.mdx:15-16", f"{D}/core.mdx:16-17"),
        ("ledger `second`", f"{D}/core.mdx:19", f"{D}/core.mdx:20"),
    ]
    assert [(label, r.old, r.why) for label, r in result.review] == [
        ("REQ-B", f"{D}/core.mdx:15-17", "overlaps hunk `-17,1 +18,1`"),
        ("ledger `second`", f"{D}/core.mdx:17", "overlaps hunk `-17,1 +18,1`"),
    ]


def test_apply_fix_without_changes_leaves_files_byte_identical(spec_repo, tmp_path):
    repo, _, target = spec_repo
    changes = si.file_changes(si.SpecRepo(repo), target, target, "v1")
    requirements, spec_map = tmp_path / "requirements.py", tmp_path / "spec_map.toml"
    requirements.write_bytes(_REQUIREMENTS_SOURCE.replace("\n", "\r\n").encode())
    spec_map.write_text(_SPEC_MAP_SOURCE)
    before = requirements.read_bytes(), spec_map.read_bytes()
    result = si.apply_fix(requirements, spec_map, changes)
    assert (requirements.read_bytes(), spec_map.read_bytes()) == before
    assert not result.rewritten and not result.review


def test_apply_fix_preserves_crlf_line_endings(spec_repo, tmp_path):
    repo, base, target = spec_repo
    changes = si.file_changes(si.SpecRepo(repo), base, target, "v1")
    requirements, spec_map = tmp_path / "requirements.py", tmp_path / "spec_map.toml"
    requirements.write_bytes(_REQUIREMENTS_SOURCE.replace("\n", "\r\n").encode())
    spec_map.write_text(_SPEC_MAP_SOURCE)
    si.apply_fix(requirements, spec_map, changes)
    fixed = requirements.read_bytes().decode()
    assert fixed.count("\r\n") == _REQUIREMENTS_SOURCE.count("\n") and f"{D}/core.mdx:16,20" in fixed


def test_cli_fix_prints_needs_review_first_and_does_not_print_the_report(spec_repo, tmp_path, monkeypatch, capsys):
    repo, base, target = spec_repo
    requirements, spec_map = tmp_path / "requirements.py", tmp_path / "spec_map.toml"
    requirements.write_text(_REQUIREMENTS_SOURCE)
    spec_map.write_text(_SPEC_MAP_SOURCE)
    monkeypatch.setattr(si, "version_files", lambda version: (requirements, spec_map))

    assert si.main([base, target, "--version", "v1", "--spec-repo", str(repo), "--fix"]) == 0

    out = capsys.readouterr().out
    assert out.startswith(f"# Citation remap (v1): `{base[:12]}` -> `{target[:12]}`")
    headings = [line for line in out.splitlines() if line.startswith("## ")]
    assert headings == ["## Needs review (2)", "## Rewritten (5)", "## Summary"]
    assert f"- REQ-B: `{D}/core.mdx:15-17` overlaps hunk `-17,1 +18,1`" in out
    assert f"- REQ-A: `{D}/core.mdx:15` -> `{D}/core.mdx:16`" in out
    assert "## 1. Changed files" not in out
    assert f"{D}/core.mdx:16,20" in requirements.read_text()


def test_parse_diff_ignores_a_deletion_header_without_an_old_path():
    assert si.parse_diff("+++ /dev/null\n@@ -1 +0,0 @@\n") == {}
