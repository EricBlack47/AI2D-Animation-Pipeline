"""Resolve and preflight the external FFmpeg tools used by the pipeline.

Resolution deliberately keeps machine-specific paths out of project files.  A
caller can provide a path explicitly, or the resolver can read the process
environment, PATH, and a small set of conventional Windows locations.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union


PathLike = Union[str, Path]
ConfigInput = Union[PathLike, Mapping[str, Any]]

TOOL_ENV_VARS = {
    "ffmpeg": "AI2D_FFMPEG_PATH",
    "ffprobe": "AI2D_FFPROBE_PATH",
}


@dataclass(frozen=True)
class ToolResolution:
    """The selected executable and the candidates considered before it."""

    name: str
    executable: Optional[str]
    source: Optional[str]
    candidates: Tuple[Dict[str, Any], ...] = ()

    @property
    def ok(self) -> bool:
        return bool(self.executable)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "path": self.executable,
            "source": self.source,
            "candidates": list(self.candidates),
        }


def load_tool_config(config: Optional[ConfigInput]) -> Dict[str, Any]:
    """Load a JSON config mapping, or normalize an already loaded mapping."""

    if config is None:
        return {}
    if isinstance(config, Mapping):
        return dict(config)

    path = Path(config).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"AI2D_CONFIG_NOT_FOUND: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"AI2D_CONFIG_INVALID: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"AI2D_CONFIG_INVALID: {path}: expected a JSON object")
    return payload


def _configured_value(config: Mapping[str, Any], tool: str) -> Optional[str]:
    """Read common explicit-path config spellings without requiring a schema."""

    aliases = (tool, f"{tool}_path", f"{tool}Path")
    containers = [config]
    for key in ("tools", "video", "external_tools"):
        value = config.get(key)
        if isinstance(value, Mapping):
            containers.append(value)

    for container in containers:
        for key in aliases:
            value = container.get(key)
            if isinstance(value, Mapping):
                value = value.get("path") or value.get("executable")
            if value is not None:
                return str(value)
    return None


def _candidate_path(value: Optional[PathLike]) -> Optional[Path]:
    if value is None:
        return None
    text = os.path.expandvars(os.path.expanduser(str(value))).strip().strip('"')
    return Path(text) if text else None


def _windows_fallbacks(
    tool: str,
    environ: Mapping[str, str],
    is_windows: Optional[bool] = None,
) -> Sequence[Path]:
    windows = os.name == "nt" if is_windows is None else is_windows
    if not windows:
        return ()

    filename = f"{tool}.exe"
    roots = []
    for key in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        value = environ.get(key)
        if value:
            roots.append(Path(value))

    candidates = []
    for root in roots:
        candidates.extend(
            [
                root / "ffmpeg" / "bin" / filename,
                root / "ffmpeg" / filename,
            ]
        )

    # These are conventional generic locations only; vendor-specific paths
    # belong in AI2D_FFMPEG_PATH/AI2D_FFPROBE_PATH or a local config file.
    candidates.extend(
        [
            Path.cwd() / filename,
            Path.cwd() / "bin" / filename,
            Path("C:/ffmpeg/bin") / filename,
            Path("C:/ffmpeg") / filename,
        ]
    )
    return candidates


def resolve_tool(
    tool: str,
    *,
    explicit_path: Optional[PathLike] = None,
    config: Optional[ConfigInput] = None,
    environ: Optional[Mapping[str, str]] = None,
    companion_path: Optional[PathLike] = None,
    is_windows: Optional[bool] = None,
) -> ToolResolution:
    """Resolve ``ffmpeg`` or ``ffprobe`` in the documented precedence order."""

    if tool not in TOOL_ENV_VARS:
        raise ValueError(f"Unsupported external tool: {tool}")

    env = dict(os.environ if environ is None else environ)
    config_data = load_tool_config(config)
    candidates = []

    def consider(value: Optional[PathLike], source: str) -> Optional[Path]:
        path = _candidate_path(value)
        if path is None:
            return None
        resolved = path.resolve()
        record = {"source": source, "path": str(resolved)}
        if resolved.is_file():
            record["ok"] = True
            candidates.append(record)
            return resolved
        record["ok"] = False
        record["reason"] = "NOT_A_FILE"
        candidates.append(record)
        return None

    selected = consider(explicit_path, "cli")
    source = "cli" if selected else None

    if selected is None:
        selected = consider(_configured_value(config_data, tool), "config")
        source = "config" if selected else None

    if selected is None:
        selected = consider(env.get(TOOL_ENV_VARS[tool]), "environment")
        source = "environment" if selected else None

    if selected is None:
        path_result = shutil.which(tool)
        if path_result:
            selected = consider(path_result, "path")
            source = "path" if selected else None
        else:
            candidates.append({"source": "path", "path": None, "ok": False, "reason": "NOT_FOUND"})

    if selected is None:
        fallback_paths = list(_windows_fallbacks(tool, env, is_windows=is_windows))
        windows = os.name == "nt" if is_windows is None else is_windows
        if windows and tool == "ffprobe" and companion_path:
            companion = _candidate_path(companion_path)
            if companion:
                fallback_paths.insert(0, companion.with_name("ffprobe.exe"))
        for fallback in fallback_paths:
            selected = consider(fallback, "windows-fallback")
            if selected:
                source = "windows-fallback"
                break

    return ToolResolution(
        name=tool,
        executable=str(selected) if selected else None,
        source=source,
        candidates=tuple(candidates),
    )


def resolve_ffmpeg(
    explicit_path: Optional[PathLike] = None,
    *,
    config: Optional[ConfigInput] = None,
    environ: Optional[Mapping[str, str]] = None,
    is_windows: Optional[bool] = None,
) -> ToolResolution:
    return resolve_tool(
        "ffmpeg",
        explicit_path=explicit_path,
        config=config,
        environ=environ,
        is_windows=is_windows,
    )


def resolve_ffprobe(
    explicit_path: Optional[PathLike] = None,
    *,
    config: Optional[ConfigInput] = None,
    environ: Optional[Mapping[str, str]] = None,
    companion_path: Optional[PathLike] = None,
    is_windows: Optional[bool] = None,
) -> ToolResolution:
    return resolve_tool(
        "ffprobe",
        explicit_path=explicit_path,
        config=config,
        environ=environ,
        companion_path=companion_path,
        is_windows=is_windows,
    )


def resolve_tools(
    *,
    ffmpeg_path: Optional[PathLike] = None,
    ffprobe_path: Optional[PathLike] = None,
    config: Optional[ConfigInput] = None,
    environ: Optional[Mapping[str, str]] = None,
    is_windows: Optional[bool] = None,
) -> Dict[str, ToolResolution]:
    """Resolve both tools once so ffprobe can use ffmpeg's directory as fallback."""

    config_data = load_tool_config(config)
    ffmpeg = resolve_ffmpeg(
        ffmpeg_path,
        config=config_data,
        environ=environ,
        is_windows=is_windows,
    )
    ffprobe = resolve_ffprobe(
        ffprobe_path,
        config=config_data,
        environ=environ,
        companion_path=ffmpeg.executable,
        is_windows=is_windows,
    )
    return {"ffmpeg": ffmpeg, "ffprobe": ffprobe}


def _version_line(output: str) -> Optional[str]:
    for line in output.splitlines():
        if "version" in line.lower():
            return line.strip()
    return next((line.strip() for line in output.splitlines() if line.strip()), None)


def run_tool_version(executable: Optional[PathLike], timeout_seconds: float = 10.0) -> Dict[str, Any]:
    """Actually invoke ``<tool> -version`` and return concise evidence."""

    if not executable:
        return {"status": "MISSING", "ok": False, "version": None, "returncode": None}
    path = str(executable)
    try:
        completed = subprocess.run(
            [path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "status": "FAIL",
            "ok": False,
            "version": None,
            "returncode": None,
            "error": str(exc),
        }

    output = (completed.stdout or "") + (completed.stderr or "")
    ok = completed.returncode == 0
    result = {
        "status": "PASS" if ok else "FAIL",
        "ok": ok,
        "version": _version_line(output),
        "returncode": completed.returncode,
    }
    if not ok:
        result["error"] = (output.strip() or "version command failed")[-2000:]
    return result


def run_ffmpeg_preflight(executable: Optional[PathLike], timeout_seconds: float = 20.0) -> Dict[str, Any]:
    """Exercise the capabilities needed by frame extraction without repo output."""

    if not executable:
        return {"status": "MISSING", "ok": False, "capabilities": {}}

    with tempfile.TemporaryDirectory(prefix="ai2d-ffmpeg-preflight-") as temporary:
        output = Path(temporary) / "frame.png"
        command = [
            str(executable),
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=2x2:r=1:d=1",
            "-vf",
            "fps=1",
            "-frames:v",
            "1",
            "-pix_fmt",
            "rgba",
            "-y",
            str(output),
        ]
        try:
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return {
                "status": "FAIL",
                "ok": False,
                "capabilities": {},
                "error": str(exc),
            }

        ok = completed.returncode == 0 and output.is_file() and output.stat().st_size > 0
        result = {
            "status": "PASS" if ok else "FAIL",
            "ok": ok,
            "capabilities": {
                "lavfi_input": ok,
                "fps_filter": ok,
                "rgba_png_output": ok,
            },
            "returncode": completed.returncode,
        }
        if not ok:
            result["error"] = (
                (completed.stderr or completed.stdout or "FFmpeg functional preflight failed").strip()
            )[-2000:]
        return result


def build_tool_preflight(
    *,
    ffmpeg_path: Optional[PathLike] = None,
    ffprobe_path: Optional[PathLike] = None,
    config: Optional[ConfigInput] = None,
    environ: Optional[Mapping[str, str]] = None,
    is_windows: Optional[bool] = None,
) -> Dict[str, Any]:
    """Resolve both tools and invoke their version/preflight commands."""

    resolutions = resolve_tools(
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
        config=config,
        environ=environ,
        is_windows=is_windows,
    )
    ffmpeg = resolutions["ffmpeg"]
    ffprobe = resolutions["ffprobe"]
    ffmpeg_version = run_tool_version(ffmpeg.executable)
    ffprobe_version = run_tool_version(ffprobe.executable)
    ffmpeg_functional = run_ffmpeg_preflight(ffmpeg.executable)

    items = []
    for resolution, version, functional in (
        (ffmpeg, ffmpeg_version, ffmpeg_functional),
        (ffprobe, ffprobe_version, None),
    ):
        item = resolution.to_dict()
        item["version_check"] = version
        if functional is not None:
            item["functional_preflight"] = functional
        items.append(item)

    ffmpeg_ok = ffmpeg.ok and ffmpeg_version["ok"] and ffmpeg_functional["ok"]
    ffprobe_ok = ffprobe.ok and ffprobe_version["ok"]
    if ffmpeg_ok and ffprobe_ok:
        status = "PASS"
    elif not ffmpeg.ok or not ffprobe.ok:
        status = "WARN"
    else:
        status = "FAIL"

    return {
        "status": status,
        "pipeline_dependencies": {
            "ffmpeg": {"required": True, "used_for": ["extract"]},
            "ffprobe": {"required": True, "used_for": ["probe_video", "extract"]},
        },
        "items": items,
    }
