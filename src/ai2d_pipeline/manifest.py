"""Animation manifest model and schema helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .frames import validate_frame_index_contiguous, discover_png_frames
from .io import load_json, write_json


def schema_path() -> Path:
    return Path(__file__).resolve().parent / "schemas" / "manifest.schema.json"


def load_schema() -> Dict[str, Any]:
    return load_json(schema_path())


@dataclass
class AnimationManifest:
    character: str
    action: str
    fps: float
    frame_count: int
    loop: bool = False
    playback_speed: float = 1.0
    hold_mode: str = "none"
    hold_duration: float = 0.0
    root_motion_enabled: bool = False
    frame_files: List[str] | None = None

    def to_payload(self) -> Dict[str, Any]:
        return {
            "schemaVersion": 1,
            "character": self.character,
            "action": self.action,
            "fps": self.fps,
            "frameCount": self.frame_count,
            "loop": self.loop,
            "playbackSpeed": self.playback_speed,
            "hold": {
                "mode": self.hold_mode,
                "duration": self.hold_duration,
            },
            "rootMotion": {
                "enabled": self.root_motion_enabled,
            },
            "frameFiles": self.frame_files or [],
        }


def build_manifest_from_frames(
    frame_dir: Path,
    character: str,
    action: str,
    fps: float,
    loop: bool = False,
) -> AnimationManifest:
    frames = discover_png_frames(frame_dir)
    issues = validate_frame_index_contiguous([frame.name for frame in frames])
    if issues:
        raise ValueError("FRAME_SEQUENCE_INVALID: " + issues[0].message)
    return AnimationManifest(
        character=character,
        action=action,
        fps=fps,
        frame_count=len(frames),
        loop=loop,
        frame_files=[path.name for path in frames],
    )


def write_manifest(path: Path, payload: Dict[str, Any]) -> Path:
    return write_json(path, payload)


def load_manifest(path: Path) -> Dict[str, Any]:
    return load_json(path)
