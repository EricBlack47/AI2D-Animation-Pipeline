# Troubleshooting

## `ffmpeg` or `ffprobe` not found

- Install ffmpeg and ensure the executable is on PATH.
- If PATH is not appropriate, set `AI2D_FFMPEG_PATH` to the ffmpeg executable
  and optionally `AI2D_FFPROBE_PATH` to the ffprobe executable.
- Keep these values in the local process environment or a local config file;
  do not commit machine-specific paths.
- `ai2d doctor` shows `status: WARN` when either tool is missing.

## `FRAME_NAME_NO_INDEX` / naming errors

- Put one sequence per directory and use a single prefix.
- Use zero-padded suffix format like `idle_0001.png`.

## `FRAME_INDEX_GAP`

- Check for missing frames or duplicate indexes.
- Preserve index continuity from first to last frame.

## Manifest validation errors

- Ensure required fields: `schemaVersion`, `character`, `action`, `fps`,
  `frameCount`, `loop`, `playbackSpeed`, `hold`, `rootMotion`, and
  `frameFiles`.
