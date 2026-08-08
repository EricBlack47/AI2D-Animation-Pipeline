import json
from pathlib import Path

import pytest
from ai2d_pipeline.manifest import AnimationManifest, build_manifest_from_frames


def test_manifest_serialization():
    manifest = AnimationManifest(
        character="demo-character",
        action="idle",
        fps=24.0,
        frame_count=8,
    )
    payload = manifest.to_payload()
    assert payload["schemaVersion"] == 1
    assert payload["character"] == "demo-character"
    assert payload["loop"] is False
    assert payload["frameFiles"] == []


def test_manifest_file_roundtrip(tmp_path: Path):
    payload = {
        "schemaVersion": 1,
        "character": "demo-character",
        "action": "attack",
        "fps": 32,
        "frameCount": 10,
        "loop": False,
        "playbackSpeed": 1.0,
        "hold": {"mode": "none", "duration": 0.0},
        "rootMotion": {"enabled": False},
        "frameFiles": ["frame_0001.png", "frame_0002.png"],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["frameCount"] == 10


def test_build_manifest_from_action_frames(tmp_path: Path):
    for idx in range(1, 5):
        path = tmp_path / f"idle_{idx:04d}.png"
        # create tiny placeholder file; manifest build only validates names at this stage
        path.write_bytes(b"\x89PNG\r\n\x1a\n")
    manifest = build_manifest_from_frames(
        frame_dir=tmp_path,
        character="hero",
        action="idle",
        fps=24.0,
        loop=False,
    )
    assert manifest.frame_count == 4
    assert manifest.frame_files == [
        "idle_0001.png",
        "idle_0002.png",
        "idle_0003.png",
        "idle_0004.png",
    ]


def test_manifest_rejects_invalid_frame_naming(tmp_path: Path):
    for name in ("idle_0001.png", "run_0002.png"):
        (tmp_path / name).touch()
    with pytest.raises(ValueError, match="FRAME_SEQUENCE_INVALID"):
        build_manifest_from_frames(
            frame_dir=tmp_path,
            character="hero",
            action="idle",
            fps=24.0,
        )
