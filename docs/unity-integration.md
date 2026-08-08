# Unity Integration

This repository does not include Unity package binaries. It defines only the data contract for downstream integration.

## Runtime contract

- `fps`: source playback rate
- `frameFiles`: ordered file names from folder
- `frameCount`: number of frames
- `loop`: loop playback
- `playbackSpeed`: playback multiplier
- `hold`: end-frame hold behavior
- `rootMotion.enabled`: reserved future runtime semantics flag

## Integration recommendation

- Keep a stable action folder per clip (one prefix set, contiguous names).
- Use `ai2d validate` before import.
- Apply `frame_*.png` or `<action>_*.png` naming consistently.
