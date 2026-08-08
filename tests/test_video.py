from ai2d_pipeline import tool_resolver
from ai2d_pipeline.tool_resolver import resolve_ffprobe


def test_ffprobe_companion_path_is_platform_aware(tmp_path, monkeypatch):
    ffmpeg = tmp_path / "ffmpeg.exe"
    ffprobe = tmp_path / "ffprobe.exe"
    ffmpeg.write_bytes(b"fake ffmpeg")
    ffprobe.write_bytes(b"fake ffprobe")
    monkeypatch.setattr(tool_resolver.shutil, "which", lambda _name: None)

    windows_result = resolve_ffprobe(
        companion_path=ffmpeg,
        environ={},
        is_windows=True,
    )
    non_windows_result = resolve_ffprobe(
        companion_path=ffmpeg,
        environ={},
        is_windows=False,
    )

    assert windows_result.executable == str(ffprobe.resolve())
    assert windows_result.source == "windows-fallback"
    assert non_windows_result.executable is None
    assert non_windows_result.source is None
