from pathlib import Path

import pytest

from ai2d_pipeline import tool_resolver
from ai2d_pipeline.tool_resolver import (
    build_tool_preflight,
    resolve_ffmpeg,
    resolve_tools,
    run_tool_version,
)


def _fake_executable(root: Path, name: str) -> Path:
    path = root / name
    path.write_bytes(b"placeholder")
    return path


def test_resolution_precedence_cli_over_config_environment_and_path(tmp_path, monkeypatch):
    cli_path = _fake_executable(tmp_path, "cli-ffmpeg.exe")
    config_path = _fake_executable(tmp_path, "config-ffmpeg.exe")
    env_path = _fake_executable(tmp_path, "env-ffmpeg.exe")
    path_path = _fake_executable(tmp_path, "path-ffmpeg.exe")
    monkeypatch.setattr(tool_resolver.shutil, "which", lambda _name: str(path_path))

    result = resolve_ffmpeg(
        cli_path,
        config={"tools": {"ffmpeg": {"path": str(config_path)}}},
        environ={"AI2D_FFMPEG_PATH": str(env_path)},
        is_windows=False,
    )

    assert result.executable == str(cli_path.resolve())
    assert result.source == "cli"


@pytest.mark.parametrize(
    ("source", "expected_name"),
    [
        ("config", "config-ffmpeg.exe"),
        ("environment", "env-ffmpeg.exe"),
        ("path", "path-ffmpeg.exe"),
    ],
)
def test_resolution_falls_through_sources(tmp_path, monkeypatch, source, expected_name):
    files = {name: _fake_executable(tmp_path, name) for name in (
        "config-ffmpeg.exe",
        "env-ffmpeg.exe",
        "path-ffmpeg.exe",
    )}
    monkeypatch.setattr(tool_resolver.shutil, "which", lambda _name: str(files["path-ffmpeg.exe"]))
    config = {"ffmpeg_path": str(files["config-ffmpeg.exe"])} if source == "config" else {}
    environ = {"AI2D_FFMPEG_PATH": str(files["env-ffmpeg.exe"])} if source in ("config", "environment") else {}
    if source == "path":
        config = {}
        environ = {}

    result = resolve_ffmpeg(config=config, environ=environ, is_windows=False)

    assert result.source == source
    assert Path(result.executable).name == expected_name


def test_ffprobe_uses_ffmpeg_sibling_as_windows_fallback(tmp_path, monkeypatch):
    ffmpeg = _fake_executable(tmp_path, "ffmpeg.exe")
    ffprobe = _fake_executable(tmp_path, "ffprobe.exe")
    monkeypatch.setattr(tool_resolver.shutil, "which", lambda _name: None)

    result = resolve_tools(
        ffmpeg_path=ffmpeg,
        environ={},
        is_windows=True,
    )["ffprobe"]

    assert result.source == "windows-fallback"
    assert result.executable == str(ffprobe.resolve())


def test_run_tool_version_reports_actual_subprocess_result(monkeypatch):
    class Completed:
        returncode = 0
        stdout = "ffmpeg version n7.0.2 test\n"
        stderr = ""

    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return Completed()

    monkeypatch.setattr(tool_resolver.subprocess, "run", fake_run)
    result = run_tool_version("ffmpeg.exe")

    assert result["status"] == "PASS"
    assert result["version"].startswith("ffmpeg version n7.0.2")
    assert calls[0][0] == ["ffmpeg.exe", "-version"]


def test_preflight_reports_both_pipeline_dependencies(monkeypatch, tmp_path):
    ffmpeg = _fake_executable(tmp_path, "ffmpeg.exe")
    ffprobe = _fake_executable(tmp_path, "ffprobe.exe")
    monkeypatch.setattr(tool_resolver, "run_tool_version", lambda _path: {
        "status": "PASS", "ok": True, "version": "test", "returncode": 0,
    })
    monkeypatch.setattr(tool_resolver, "run_ffmpeg_preflight", lambda _path: {
        "status": "PASS", "ok": True, "capabilities": {"test": True},
    })

    result = build_tool_preflight(
        ffmpeg_path=ffmpeg,
        ffprobe_path=ffprobe,
        is_windows=False,
    )

    assert result["status"] == "PASS"
    assert result["pipeline_dependencies"]["ffprobe"]["required"] is True
    assert [item["name"] for item in result["items"]] == ["ffmpeg", "ffprobe"]
