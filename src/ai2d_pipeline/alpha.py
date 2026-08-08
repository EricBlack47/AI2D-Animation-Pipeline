"""Optional alpha-processing stage abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .frames import discover_png_frames
from .io import write_json


class AlphaProcessor(ABC):
    @abstractmethod
    def apply(self, frame_paths, output_dir: Path):
        raise NotImplementedError

    @property
    @abstractmethod
    def mode(self) -> str:
        raise NotImplementedError


class NoOpAlphaProcessor(AlphaProcessor):
    mode = "none"

    def apply(self, frame_paths, output_dir: Path):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for source in frame_paths:
            target = output_dir / source.name
            target.write_bytes(source.read_bytes())
            written.append(target.name)
        write_json(output_dir / "alpha_report.json", {"status": "NO_ALPHA_PROCESSING", "count": len(written), "frames": written})
        return output_dir
