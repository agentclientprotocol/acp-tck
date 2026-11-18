#!/usr/bin/env python3
"""Conforming fixture: a `session/resume` replay rebuilds a session message, a tool call's content,
a terminal's output and a compaction's summary from chunks, each opened by its emptied
whole-entity update (session-setup.mdx:303-321). `ACP-RESUME-205` PASSes non-vacuously.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _entity_chunks import ReplaysEntityChunksMixin  # noqa: E402


class ReplaysEntityChunksAgent(ReplaysEntityChunksMixin, ConformingAgent):
    pass


def main() -> None:
    ReplaysEntityChunksAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
