"""Command line interface for the OSS pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .alpha import NoOpAlphaProcessor
from .frames import discover_png_frames, validate_canvas_consistency, validate_frame_index_contiguous, validate_alpha_paths
from .io import write_json
from .manifest import build_manifest_from_frames, load_manifest, load_schema, write_manifest
from .tool_resolver import build_tool_preflight, load_tool_config
from .validation import Severity, ValidationIssue, as_dict, has_error
from .video import extract_frames


def _path(value: str | None) -> Path | None:
    return Path(value).resolve() if value else None


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def command_doctor(args=None) -> int:
    args = args or argparse.Namespace(config=None, ffmpeg_path=None, ffprobe_path=None)
    try:
        config = load_tool_config(_path(getattr(args, "config", None)))
        preflight = build_tool_preflight(
            ffmpeg_path=getattr(args, "ffmpeg_path", None),
            ffprobe_path=getattr(args, "ffprobe_path", None),
            config=config,
        )
    except (OSError, ValueError) as exc:
        _print({"status": "FAIL", "error": str(exc), "items": []})
        return 1

    issues = []
    issues.append({
        "component": "python",
        "ok": True,
        "version": sys.version.split()[0],
    })
    issues.append({"component": "pillow", "ok": True, "status": "AVAILABLE"})
    for item in preflight["items"]:
        issues.append({"component": item["name"], **item})
    result = dict(preflight)
    result["items"] = issues
    _print(result)
    return 0 if result["status"] == "PASS" else 1


def command_extract(args) -> int:
    output = _path(args.output)
    config = load_tool_config(_path(getattr(args, "config", None)))
    payload = extract_frames(
        _path(args.input),
        fps=args.fps if args.fps else "source",
        output_dir=output,
        overwrite=bool(args.overwrite),
        ffmpeg_path=getattr(args, "ffmpeg_path", None),
        ffprobe_path=getattr(args, "ffprobe_path", None),
        config=config,
    )
    if args.alpha == "noop":
        frames = discover_png_frames(output)
        NoOpAlphaProcessor().apply(frames, output)
        payload["alpha"] = "noop"
    _print(payload)
    return 0


def command_validate(args) -> int:
    issues = []
    target = _path(args.target)
    if target.is_dir():
        frames = discover_png_frames(target)
        names = [path.name for path in frames]
        issues.extend(validate_frame_index_contiguous(names))
        issues.extend(validate_canvas_consistency(frames))
        issues.extend(validate_alpha_paths(frames, require_alpha=not args.allow_no_alpha))
        serialized = [as_dict(item) for item in issues]
        failed = has_error(issues)
        result = {
            "status": "FAIL" if failed else "PASS",
            "type": "frames",
            "count": len(frames),
            "issues": serialized,
        }
        _print(result)
        return 1 if failed else 0

    payload = load_manifest(target)
    schema = load_schema()
    try:
        from jsonschema import Draft202012Validator
    except Exception:
        Draft202012Validator = None
    if Draft202012Validator is None:
        # minimal fallback
        required = set(schema["required"])
        missing = sorted(required - set(payload.keys()))
        if missing:
            raise RuntimeError(f"SCHEMA_REQUIRED_MISSING: {missing}")
        result = {"status": "PASS", "type": "manifest", "issues": []}
    else:
        errors = list(Draft202012Validator(schema).iter_errors(payload))
        issues = [
            ValidationIssue(
                code=f"SCHEMA_{error.validator.upper()}",
                severity=Severity.ERROR,
                message=str(error.message),
                file=str(target),
                expected=str(error.validator_value),
                actual=str(error.instance),
                remediation="Fix manifest fields to match schema.",
            )
            for error in errors
        ]
        result = {
            "status": "FAIL" if has_error(issues) else "PASS",
            "type": "manifest",
            "issues": [as_dict(item) for item in issues],
        }
    _print(result)
    return 0 if result["status"] == "PASS" else 1


def command_manifest(args) -> int:
    payload = build_manifest_from_frames(
        frame_dir=_path(args.frames),
        character=args.character,
        action=args.action,
        fps=float(args.fps),
        loop=bool(args.loop),
    ).to_payload()
    output = _path(args.output) if args.output else _path(args.frames) / "manifest.json"
    write_manifest(output, payload)
    # optional validate output schema (best effort)
    try:
        payload["frameFiles"] = payload.get("frameFiles", [])
    except Exception:
        pass
    _print({"status": "MANIFEST_WRITTEN", "path": str(output), "frameCount": payload["frameCount"]})
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai2d", description="AI2D animation pipeline")
    parser.add_argument("--version", action="version", version=f"ai2d {__version__}")
    _add_tool_options(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Check environment and dependencies")
    _add_tool_options(doctor, suppress_defaults=True)
    doctor.set_defaults(func=command_doctor)

    extract = sub.add_parser("extract", help="Extract frames from MP4")
    _add_tool_options(extract, suppress_defaults=True)
    extract.add_argument("input", help="Input MP4 path")
    extract.add_argument("output", help="Output frame directory")
    extract.add_argument("--fps", default="source", help='fps value or "source"')
    extract.add_argument("--alpha", choices=["none", "noop"], default="none")
    extract.add_argument("--overwrite", action="store_true")
    extract.set_defaults(func=command_extract)

    validate = sub.add_parser("validate", help="Validate frames directory or manifest")
    validate.add_argument("target", help="Directory (frames) or manifest.json path")
    validate.add_argument("--allow-no-alpha", action="store_true")
    validate.set_defaults(func=command_validate)

    manifest = sub.add_parser("manifest", help="Create manifest for frame directory")
    manifest.add_argument("frames", help="Frames directory")
    manifest.add_argument("--character", required=True)
    manifest.add_argument("--action", required=True)
    manifest.add_argument("--fps", required=True, help="Runtime fps")
    manifest.add_argument("--loop", action="store_true")
    manifest.add_argument("--output", help="Write path for manifest.json")
    manifest.set_defaults(func=command_manifest)

    args = parser.parse_args(argv)
    return int(args.func(args))


def _add_tool_options(parser, suppress_defaults: bool = False) -> None:
    default = argparse.SUPPRESS if suppress_defaults else None
    parser.add_argument(
        "--config",
        default=default,
        help="JSON config path; explicit tool paths take precedence over environment/PATH.",
    )
    parser.add_argument(
        "--ffmpeg-path",
        default=default,
        help="Explicit ffmpeg executable path.",
    )
    parser.add_argument(
        "--ffprobe-path",
        default=default,
        help="Explicit ffprobe executable path.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
