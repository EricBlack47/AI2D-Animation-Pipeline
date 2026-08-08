# AI2D Animation Pipeline

A production-oriented pipeline for converting AI-generated or standard 2D animation sources into validated, Unity-ready sprite animations.

## What it solves

- video/image sequence -> frame extraction
- optional alpha processing
- manifest validation
- CLI-driven validation and reproducibility
- demo generation with no dependency on proprietary assets

## Minimal pipeline

```mermaid
flowchart TD
    A[AI Video / MP4 / Image Sequence] --> B[Frame Extraction]
    B --> C[Alpha Processing (optional)]
    C --> D[Validation]
    D --> E[Animation Manifest]
    E --> F[Unity Runtime]
```

## Quick Start

```bash
# install deps
python -m pip install -e .

# check environment
python -m ai2d_pipeline.cli doctor

# generate synthetic demo assets (for local test only)
python tools/generate_demo_assets.py --output examples/demo-character

# extract frames
python -m ai2d_pipeline.cli extract path/to/input.mp4 ./.cache/extracted --fps source

# validate extracted frames
python -m ai2d_pipeline.cli validate ./.cache/extracted

# Frame naming rule (required for validation and manifest):
# `frame_0000.png`, `idle_0001.png`, or other `<prefix>_<zero-padded index>`.

# generate manifest
python -m ai2d_pipeline.cli manifest ./.cache/extracted --character demo-character --action idle --fps 32 --output ./.cache/extracted/manifest.json
```

If ffmpeg is not on PATH, set `AI2D_FFMPEG_PATH` and optionally
`AI2D_FFPROBE_PATH` in the process environment. Machine-specific paths stay
outside the repository.

## Commands

- `python -m ai2d_pipeline.cli doctor`
- `python -m ai2d_pipeline.cli extract <input> <output> [--fps source|24|30] [--alpha noop]`
- `python -m ai2d_pipeline.cli validate <target>` (directory -> frame validation, JSON -> manifest validation)
- `python -m ai2d_pipeline.cli manifest --character <name> --action <name> --fps <fps> <frame_dir>`

## Documentation

- [Architecture](docs/architecture.md)
- [Pipeline](docs/pipeline.md)
- [Manifest](docs/manifest.md)
- [Validation](docs/validation.md)
- [Unity Integration](docs/unity-integration.md)
- [Troubleshooting](docs/troubleshooting.md)

## License

Apache-2.0
