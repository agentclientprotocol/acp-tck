"""Parsing of requirement and ledger citation strings (see `make_cite` in
`tck.common.requirements`).

A citation is free text pinned to a spec revision, e.g.
`docs/protocol/v1/draft/prompt-turn.mdx:578-590,598; schema/v1/schema.unstable.json#/$defs/StopReason
(Req 24) @ <commit>`. Two kinds of reference are machine-readable: spec-repo file paths with
optional 1-based line ranges, and JSON Pointers into a version's `schema.unstable.json`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_POINTER = re.compile(r"(?:\bschema/(v\d+)/)?schema\.unstable\.json#(/[^\s`'\"),;]*)")
_DEFS_PREFIX = "/$defs/"


def schema_pointers(text: str, version: str) -> list[str]:
    """JSON Pointers into `version`'s (`"v1"`, `"v2"`) `schema.unstable.json` cited in `text`.

    A pointer counts when its file is `schema/<version>/schema.unstable.json` or a bare
    `schema.unstable.json`; pointers into another version's schema are skipped.
    """
    return [
        pointer.rstrip(".")
        for cited_version, pointer in _POINTER.findall(text)
        if cited_version in ("", version)
    ]


def resolve_pointer(document: Any, pointer: str) -> Any:
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


def pointer_def(pointer: str) -> str | None:
    """The `$defs` name a pointer points into (`/$defs/A/properties/b` -> `A`), or `None` for a
    pointer outside `$defs` (the schema root)."""
    if not pointer.startswith(_DEFS_PREFIX):
        return None
    name = pointer[len(_DEFS_PREFIX) :].split("/", 1)[0]
    return name.replace("~1", "/").replace("~0", "~") or None


@dataclass(frozen=True)
class LineRef:
    path: str
    """Spec-repo path, e.g. `docs/protocol/v1/draft/overview.mdx`."""
    ranges: tuple[tuple[int, int], ...]
    """1-based inclusive line ranges; empty when the citation names the whole file."""


# A path starts at a token boundary, so `agent-client-protocol-schema/...` (Rust source) and
# pointer citations (`schema.unstable.json#...`) are not mistaken for one.
_LINE_REF = re.compile(
    r"(?<![\w./-])((?:docs|schema)/[\w./-]*\.(?:mdx|json))(?![\w#])"
    r"(?::(\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*))?"
)


@dataclass(frozen=True)
class LineRefMatch:
    ref: LineRef
    spec_span: tuple[int, int] | None
    """Where the line spec (`578-590,598`, without the colon) sits in the searched text; `None`
    for a whole-file citation."""


def find_line_refs(text: str) -> list[LineRefMatch]:
    """Like `line_refs`, but also locates each line spec in `text` (to rewrite it in place)."""
    matches = []
    for m in _LINE_REF.finditer(text):
        spec = m.group(2)
        ranges = []
        for part in spec.split(",") if spec else ():
            start, _, end = part.partition("-")
            ranges.append((int(start), int(end or start)))
        matches.append(LineRefMatch(LineRef(m.group(1), tuple(ranges)), m.span(2) if spec else None))
    return matches


def line_refs(text: str) -> list[LineRef]:
    """Spec-repo file citations in `text` (`docs/...` or `schema/...`, `.mdx`/`.json`), with
    their line ranges. Schema JSON Pointer citations are not included (see `schema_pointers`)."""
    return [match.ref for match in find_line_refs(text)]
