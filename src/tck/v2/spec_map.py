"""Access to this version's `spec_map.toml` (see `tck.common.spec_map`)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ..common.spec_map import SpecMap, load_spec_map

SPEC_MAP_PATH = Path(__file__).parent / "spec_map.toml"


@lru_cache(maxsize=1)
def load() -> SpecMap:
    return load_spec_map(SPEC_MAP_PATH)
