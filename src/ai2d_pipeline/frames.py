"""Frame discovery and frame-sequence validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from PIL import Image

from .validation import ValidationIssue, Severity


def natural_sort_key(value: str) -> List:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def discover_png_frames(directory: Path) -> List[Path]:
    directory = Path(directory)
    files = [path for path in directory.glob("*.png")]
    files.sort(key=lambda path: natural_sort_key(path.name))
    return files


_FRAME_SEQUENCE_RE = re.compile(r"^(?P<prefix>.+)_(?P<index>\d+)$")


def validate_frame_index_contiguous(names: List[str]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not names:
        issues.append(ValidationIssue(
            code="FRAMES_EMPTY",
            severity=Severity.ERROR,
            message="No PNG frames found.",
            expected="At least one frame",
            actual="0",
            remediation="Check extract output path and input content.",
        ))
        return issues

    parsed = []
    for name in names:
        stem = Path(name).stem
        match = _FRAME_SEQUENCE_RE.match(stem)
        if not match:
            issues.append(ValidationIssue(
                code="FRAME_NAME_NO_INDEX",
                severity=Severity.ERROR,
                message=f"Frame name must match `<prefix>_<index>` pattern: {name}",
                file=name,
                expected="attack_0001.png, idle_0001.png",
                actual=name,
                remediation="Use zero-padded numeric suffix and keep prefix+index form, e.g. `idle_0001.png`.",
            ))
        else:
            parsed.append((name, match.group("prefix"), int(match.group("index")), len(match.group("index"))))

    if issues:
        return issues

    prefixes = {item[1] for item in parsed}
    widths = {item[3] for item in parsed}
    if len(prefixes) > 1:
        issues.append(ValidationIssue(
            code="FRAME_NAME_PREFIX_MISMATCH",
            severity=Severity.ERROR,
            message="Frame files must share a single prefix.",
            file=", ".join(names),
            expected="Consistent prefix for all frames in directory",
            actual=", ".join(sorted(prefixes)),
            remediation="Split mixed-prefix sequences into separate directories or rename one set.",
        ))
    if len(widths) > 1:
        issues.append(ValidationIssue(
            code="FRAME_NAME_INDEX_WIDTH_MISMATCH",
            severity=Severity.ERROR,
            message="Index zero-padding width must be consistent.",
            file=", ".join(names),
            expected="All indexes with same number of digits (e.g. 0001)",
            actual=", ".join(str(item[3]) for item in parsed),
            remediation="Keep width consistent for a single sequence.",
        ))

    if issues:
        return issues

    indexes = [item[2] for item in parsed]
    width = {item[3] for item in parsed}
    first = indexes[0]
    expected = list(range(first, first + len(indexes)))
    if indexes != expected:
        pad = width.pop()
        issues.append(ValidationIssue(
            code="FRAME_INDEX_GAP",
            severity=Severity.ERROR,
            message="Frame indexes are not contiguous or not ordered.",
            file=", ".join(sorted(names)),
            expected=", ".join(f"{item:0{pad}d}" for item in expected),
            actual=", ".join(f"{item:0{pad}d}" for item in indexes),
            remediation="Rename files to contiguous sequence with same prefix and index width.",
        ))
    return issues


def validate_canvas_consistency(paths: List[Path]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not paths:
        return issues
    with Image.open(paths[0]) as image:
        target = image.size
        mode = image.mode
    for item in paths[1:]:
        with Image.open(item) as image:
            if image.size != target:
                issues.append(ValidationIssue(
                    code="FRAME_CANVAS_MISMATCH",
                    severity=Severity.ERROR,
                    message=f"Canvas changed: {item.name} is {image.size}, expected {target}.",
                    file=str(item),
                    expected=f"{target}",
                    actual=f"{image.size}",
                    remediation="Normalize all frames to same canvas before validation.",
                ))
            if image.mode != mode:
                issues.append(ValidationIssue(
                    code="FRAME_MODE_MISMATCH",
                    severity=Severity.WARNING,
                    message=f"Mode changed: {item.name} is {image.mode}, expected {mode}.",
                    file=str(item),
                    expected=mode,
                    actual=image.mode,
                    remediation="Convert frames to a consistent pixel format.",
                ))
    return issues


def validate_alpha_paths(paths: List[Path], require_alpha: bool = True) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not paths:
        return issues
    for path in paths:
        with Image.open(path) as image:
            bands = image.getbands()
            has_alpha = "A" in bands
        if require_alpha and not has_alpha:
            issues.append(ValidationIssue(
                code="FRAME_MISSING_ALPHA",
                severity=Severity.WARNING,
                message=f"Frame has no alpha channel: {path.name}.",
                file=str(path),
                expected="RGBA/RGBA-like with alpha",
                actual=",".join(bands),
                remediation="Run alpha-processing step if transparent assets are expected.",
            ))
    return issues
