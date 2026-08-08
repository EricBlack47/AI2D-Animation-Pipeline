# Validation

`ai2d validate` has two modes:

- Directory mode: validates PNG frame sequence in a folder.
- Manifest mode: validates a JSON manifest against schema.

## Directory checks

- `FRAMES_EMPTY`: no `.png` found
- `FRAME_NAME_NO_INDEX`: file name must match `<prefix>_<digits>`
- `FRAME_NAME_PREFIX_MISMATCH`: mixed action prefixes in one folder
- `FRAME_NAME_INDEX_WIDTH_MISMATCH`: inconsistent zero-padding width
- `FRAME_INDEX_GAP`: indexes not contiguous
- `FRAME_CANVAS_MISMATCH`: image size changed
- `FRAME_MODE_MISMATCH`: color mode changed
- `FRAME_MISSING_ALPHA`: optional check can be disabled with `--allow-no-alpha`

## Exit codes

- `0`: pass
- `1`: validation error
