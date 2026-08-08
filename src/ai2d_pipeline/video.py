"""Video probing and frame extraction."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Union

from .frames import discover_png_frames
from .tool_resolver import (
    ConfigInput,
    PathLike,
    resolve_ffmpeg,
    resolve_ffprobe,
)


def ffprobe_executable(
    explicit_path: Optional[PathLike] = None,
    *,
    config: Optional[ConfigInput] = None,
    environ: Optional[Mapping[str, str]] = None,
    companion_path: Optional[PathLike] = None,
) -> Optional[str]:
    return resolve_ffprobe(
        explicit_path,
        config=config,
        environ=environ,
        companion_path=companion_path,
    ).executable


def ffmpeg_executable(
    explicit_path: Optional[PathLike] = None,
    *,
    config: Optional[ConfigInput] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> Optional[str]:
    return resolve_ffmpeg(explicit_path, config=config, environ=environ).executable


def _run_json(cmd: List[str]) -> Dict:
    completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "ffprobe failed")
    return __import__("json").loads(completed.stdout)


def probe_video(
    video_path: Path,
    *,
    ffprobe_path: Optional[PathLike] = None,
    config: Optional[ConfigInput] = None,
    environ: Optional[Mapping[str, str]] = None,
    companion_path: Optional[PathLike] = None,
) -> Dict:
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"VIDEO_NOT_FOUND: {video_path}")
    companion = companion_path or ffmpeg_executable(config=config, environ=environ)
    exe = ffprobe_executable(
        ffprobe_path,
        config=config,
        environ=environ,
        companion_path=companion,
    )
    if not exe:
        raise FileNotFoundError("FFPROBE_NOT_FOUND")
    payload = _run_json([
        exe,
        "-v", "error",
        "-print_format", "json",
        "-show_entries", "stream=width,height,codec_name,r_frame_rate,duration",
        "-show_entries", "format=duration,format_name",
        "-select_streams", "v:0",
        str(video_path),
    ])
    streams = payload.get("streams", [])
    if not streams:
        raise RuntimeError("NO_VIDEO_STREAM")
    stream = streams[0]
    width = int(stream.get("width", 0))
    height = int(stream.get("height", 0))
    codec = str(stream.get("codec_name", "unknown"))
    r_frame_rate = str(stream.get("r_frame_rate", "0/1"))
    numerator, denominator = 1.0, 1.0
    if "/" in r_frame_rate:
        try:
            n, d = r_frame_rate.split("/")
            numerator = float(n)
            denominator = float(d or 1.0)
        except Exception:
            numerator, denominator = 30.0, 1.0
    else:
        try:
            numerator = float(r_frame_rate)
            denominator = 1.0
        except Exception:
            numerator, denominator = 30.0, 1.0
    fps = round(numerator / max(denominator, 1.0), 3)
    duration = float(payload.get("format", {}).get("duration", payload.get("streams", [{}])[0].get("duration", 0.0) or 0.0))
    return {
        "file": str(video_path),
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "codec": codec,
        "fps": fps,
        "format_name": payload.get("format", {}).get("format_name"),
    }


def resolve_fps(video_probe: Dict, fps: str) -> str:
    if fps in ("source", "src", "native"):
        return str(video_probe["fps"])
    return fps


def extract_frames(
    video_path: Path,
    fps: Union[float, str],
    output_dir: Path,
    overwrite: bool = False,
    *,
    ffmpeg_path: Optional[PathLike] = None,
    ffprobe_path: Optional[PathLike] = None,
    config: Optional[ConfigInput] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> Dict:
    video_path = Path(video_path).resolve()
    output_dir = Path(output_dir).resolve()
    if not video_path.is_file():
        raise FileNotFoundError(f"VIDEO_NOT_FOUND: {video_path}")
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise RuntimeError(f"OUTPUT_NOT_EMPTY: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    exe = ffmpeg_executable(ffmpeg_path, config=config, environ=environ)
    if not exe:
        raise FileNotFoundError("FFMPEG_NOT_FOUND")
    probe = probe_video(
        video_path,
        ffprobe_path=ffprobe_path,
        config=config,
        environ=environ,
        companion_path=exe,
    )
    effective_fps = resolve_fps(probe, str(fps))
    cmd = [
        exe,
        "-hide_banner", "-loglevel", "error",
        "-i", str(video_path),
        "-vf", f"fps={effective_fps}",
        "-pix_fmt", "rgba",
        "-start_number", "0000",
        str(output_dir / "frame_%04d.png"),
    ]
    completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip() or "FFMPEG_FAILED")
    frames = discover_png_frames(output_dir)
    return {
        "status": "VIDEO_FRAMES_EXTRACTED",
        "source": str(video_path),
        "output": str(output_dir),
        "fps_used": effective_fps,
        "video_info": probe,
        "frame_count": len(frames),
    }
