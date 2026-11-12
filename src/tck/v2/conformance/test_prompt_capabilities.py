"""Prompt content capabilities: `image`, `audio`, `embeddedContext`
(ACP-PROMPTCAP-001/002/003, ACP-PROMPTCAP-201) -- gated on the **object-marker** capability
`capabilities.session.prompt.{image,audio,embeddedContext}`, since v2 has no boolean-encoded
capabilities anywhere (see `ACP-INIT-204`).

A non-error `session/prompt` result is sufficient for 001..003: `run_prompt`'s turn-end predicate
(`_helpers.py`) only returns once the turn has reached idle, so there is no separate
`stopReason` to check on the response itself as in v1 (v2's response is only an acceptance
receipt, `ACP-PROMPT-201`).

`ACP-PROMPTCAP-201` is the inverse: an agent MUST reject a content type that is neither baseline
nor advertised with `-32602`, without inserting it (prompt-lifecycle.mdx:313). It is a runtime
negative gate -- each block type is probed only when its capability is *not* advertised.
"""

from __future__ import annotations

import base64
import struct
import zlib

import pytest

from ._helpers import (
    assert_prompt_rejected_not_inserted,
    connected_agent,
    new_session,
    run_prompt,
)


def _tiny_png_base64() -> str:
    """A minimal valid 1x1 white PNG, built at runtime (not a hardcoded blob) so the bytes are
    self-evidently a real, decodable PNG rather than an opaque fixture nobody can verify."""

    def _chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)  # 1x1, 8-bit, truecolor
    raw_scanline = b"\x00" + b"\xff\xff\xff"  # filter byte + one white RGB pixel
    idat = zlib.compress(raw_scanline)
    png_bytes = signature + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")
    return base64.b64encode(png_bytes).decode("ascii")


def _tiny_wav_base64() -> str:
    """A minimal valid 8-sample, mono, 8-bit PCM WAV file, built at runtime."""
    samples = bytes([128] * 8)  # silence
    data_chunk = b"data" + struct.pack("<I", len(samples)) + samples
    fmt_chunk = b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 8000, 1, 8)
    riff_body = b"WAVE" + fmt_chunk + data_chunk
    wav_bytes = b"RIFF" + struct.pack("<I", len(riff_body)) + riff_body
    return base64.b64encode(wav_bytes).decode("ascii")


@pytest.mark.requirement("ACP-PROMPTCAP-001")
@pytest.mark.capability("capabilities.session.prompt.image")
async def test_prompt_with_image_block_resolves(agent_launch, tmp_path):
    """ACP-PROMPTCAP-001."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        blocks = [
            {"type": "text", "text": "describe this image"},
            {"type": "image", "data": _tiny_png_base64(), "mimeType": "image/png"},
        ]
        turn = await run_prompt(agent, session_id, blocks, timeout=agent_launch.default_timeout)
        msg = turn.response_entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/prompt with an image block did not succeed: {turn.response_entry.text!r}"
        )


@pytest.mark.requirement("ACP-PROMPTCAP-002")
@pytest.mark.capability("capabilities.session.prompt.audio")
async def test_prompt_with_audio_block_resolves(agent_launch, tmp_path):
    """ACP-PROMPTCAP-002."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        blocks = [
            {"type": "text", "text": "describe this audio"},
            {"type": "audio", "data": _tiny_wav_base64(), "mimeType": "audio/wav"},
        ]
        turn = await run_prompt(agent, session_id, blocks, timeout=agent_launch.default_timeout)
        msg = turn.response_entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/prompt with an audio block did not succeed: {turn.response_entry.text!r}"
        )


@pytest.mark.requirement("ACP-PROMPTCAP-003")
@pytest.mark.capability("capabilities.session.prompt.embeddedContext")
async def test_prompt_with_embedded_resource_block_resolves(agent_launch, tmp_path):
    """ACP-PROMPTCAP-003."""
    resource_path = tmp_path / "context.txt"
    resource_path.write_text("some embedded context")
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        blocks = [
            {"type": "text", "text": "use this context"},
            {
                "type": "resource",
                "resource": {
                    "uri": resource_path.as_uri(),
                    "text": "some embedded context",
                    "mimeType": "text/plain",
                },
            },
        ]
        turn = await run_prompt(agent, session_id, blocks, timeout=agent_launch.default_timeout)
        msg = turn.response_entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/prompt with a resource block did not succeed: {turn.response_entry.text!r}"
        )


def _resource_block(tmp_path) -> dict:
    return {
        "type": "resource",
        "resource": {
            "uri": (tmp_path / "context.txt").as_uri(),
            "text": "some embedded context",
            "mimeType": "text/plain",
        },
    }


def _advertised(init_result: dict | None, path: str) -> bool:
    """Whether `path` holds a capability object. v2's prompt capabilities are `object | null`
    (a client reads `true` as not advertised), so only an object counts."""
    value: object = init_result
    for part in path.split("."):
        if not isinstance(value, dict):
            return False
        value = value.get(part)
    return isinstance(value, dict)


_UNADVERTISED_CASES = {
    "image": (
        "capabilities.session.prompt.image",
        lambda tmp_path: {"type": "image", "data": _tiny_png_base64(), "mimeType": "image/png"},
    ),
    "audio": (
        "capabilities.session.prompt.audio",
        lambda tmp_path: {"type": "audio", "data": _tiny_wav_base64(), "mimeType": "audio/wav"},
    ),
    "resource": ("capabilities.session.prompt.embeddedContext", _resource_block),
}


@pytest.mark.requirement("ACP-PROMPTCAP-201")
@pytest.mark.capability("capabilities.session")
@pytest.mark.parametrize("block_type", list(_UNADVERTISED_CASES))
async def test_unadvertised_content_block_is_rejected_without_insertion(
    block_type, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-PROMPTCAP-201. A well-formed `image`/`audio`/`resource` block the agent did not
    advertise under `capabilities.session.prompt` is answered `-32602` and not inserted
    (prompt-lifecycle.mdx:313; content.mdx:22). The gate is inverted -- the case runs only for a
    capability that is *absent* -- so it is computed here from the cached `initialize` result
    (`_advertised`) instead of by a capability marker, which only gates on presence; the marker
    above is the baseline `session` one. Only an object value counts as advertised: `true` is
    read as not advertised, so such an agent is probed. SKIPs for a type the agent advertises
    (`ACP-PROMPTCAP-001..003` judge that side). A client never sends an unadvertised block; the
    probe breaks that rule on purpose because the spec defines the agent's answer."""
    capability_path, make_block = _UNADVERTISED_CASES[block_type]
    if _advertised(agent_initialize_result.result, capability_path):
        pytest.skip(f"{capability_path} is advertised -- ACP-PROMPTCAP-001..003 judge accepting it")
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        await assert_prompt_rejected_not_inserted(
            agent,
            session_id,
            [{"type": "text", "text": "use this"}, make_block(tmp_path)],
            what=f"a prompt with an unadvertised {block_type!r} block ({capability_path})",
            timeout=timeout,
        )
