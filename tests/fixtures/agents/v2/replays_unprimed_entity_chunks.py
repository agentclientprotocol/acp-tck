#!/usr/bin/env python3
"""Non-conforming fixture: a `session/resume` replay sends chunks of a session message, a tool
call's content, a terminal's output and a compaction's summary without the whole-entity update
that must open them (session-setup.mdx:303-321). The environment variable
`TCK_FIXTURE_UNPRIMED_CHUNK` limits that to one chunk kind (the others stay primed). Violates
`ACP-RESUME-205` only.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _entity_chunks import ReplaysEntityChunksMixin  # noqa: E402


_ONLY = os.environ.get("TCK_FIXTURE_UNPRIMED_CHUNK")


class ReplaysUnprimedEntityChunksAgent(ReplaysEntityChunksMixin, ConformingAgent):
    UNPRIMED = (_ONLY,) if _ONLY else ReplaysEntityChunksMixin.KINDS


def main() -> None:
    ReplaysUnprimedEntityChunksAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
