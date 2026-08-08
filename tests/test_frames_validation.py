import tempfile
from pathlib import Path

from ai2d_pipeline.frames import validate_frame_index_contiguous, discover_png_frames


def test_contiguous_indexes():
    names = ["frame_0001.png", "frame_0002.png", "frame_0003.png"]
    issues = validate_frame_index_contiguous(names)
    assert issues == []


def test_demo_style_indexes():
    names = ["idle_0001.png", "idle_0002.png", "idle_0003.png"]
    issues = validate_frame_index_contiguous(names)
    assert issues == []


def test_non_contiguous_indexes():
    names = ["frame_0001.png", "frame_0003.png", "frame_0004.png"]
    issues = validate_frame_index_contiguous(names)
    assert issues
    assert issues[0].code == "FRAME_INDEX_GAP"


def test_mixed_prefix_is_rejected():
    names = ["idle_0001.png", "attack_0002.png"]
    issues = validate_frame_index_contiguous(names)
    assert issues
    assert issues[0].code == "FRAME_NAME_PREFIX_MISMATCH"


def test_mixed_width_is_rejected():
    names = ["idle_01.png", "idle_002.png"]
    issues = validate_frame_index_contiguous(names)
    assert issues
    assert issues[0].code == "FRAME_NAME_INDEX_WIDTH_MISMATCH"


def test_discover_png_frames_sorted():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "frame_0002.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (root / "frame_0001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        found = discover_png_frames(root)
        assert [path.name for path in found] == ["frame_0001.png", "frame_0002.png"]
