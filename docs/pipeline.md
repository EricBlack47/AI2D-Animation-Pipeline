# Pipeline

The OSS pipeline is intentionally conservative:

- No hard dependency on proprietary game project files
- No embedded API keys or credentials
- Media files are generated in working directories and excluded from Git
- All outputs are explicit and reproducible

## Stages

### 1) Input normalization
- MP4: `python -m ai2d_pipeline.cli extract`
- Image sequence: provide a PNG folder directly to manifest/validation
- `extract` uses both FFmpeg and FFprobe: FFprobe supplies source metadata and
  FFmpeg performs frame extraction.

### External video tools

The resolver checks explicit CLI/config paths first, then
`AI2D_FFMPEG_PATH`/`AI2D_FFPROBE_PATH`, PATH, and generic Windows fallback
locations. `ai2d doctor` invokes both tools with `-version` and runs a small
FFmpeg functional preflight for the `lavfi` input, `fps` filter, and RGBA PNG
output capabilities. No local executable path is stored in the repository.

### 2) Optional alpha
- No-op mode by default (`--alpha noop`) in this initial release
- Alpha-processing adapters are extensible in future versions

### 3) Validation
- Frame sequence continuity
- Canvas consistency
- Manifest schema checks
- Frame sequence names must share one `<prefix>_####` format per folder
  - Examples: `frame_0000.png`, `idle_0001.png`, `attack_0012.png`
- Prefix and zero-pad width are validated to keep generated manifests predictable

### 4) Manifest
- Canonical manifest includes fps, frame count, loop/hold/rootMotion metadata and frame file list
