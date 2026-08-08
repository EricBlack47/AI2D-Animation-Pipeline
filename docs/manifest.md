# Manifest

`AnimationManifest` is the pipeline contract consumed by downstream runtime tooling.

## Schema

`schemaVersion`, `character`, `action`, `fps`, and `frameCount` are required.

- `schemaVersion`: integer >= 1
- `character`: source character key (string)
- `action`: action id (string)
- `fps`: positive number
- `frameCount`: count of frame files in directory
- `loop`: boolean
- `playbackSpeed`: positive number
- `hold`: `{ "mode": "none" | "hold" | "holdLoop", "duration": number }`
- `rootMotion`: `{ "enabled": boolean }`
- `frameFiles`: file names in sequence order

## Example

```json
{
  "schemaVersion": 1,
  "character": "demo_character",
  "action": "attack",
  "fps": 32,
  "frameCount": 10,
  "loop": false,
  "playbackSpeed": 1.0,
  "hold": {
    "mode": "none",
    "duration": 0.0
  },
  "rootMotion": {
    "enabled": false
  },
  "frameFiles": ["attack_0001.png", "attack_0002.png"]
}
```

## Usage

- Generate: `python -m ai2d_pipeline.cli manifest <frames_dir> --character demo --action attack --fps 32`
- Validate: `python -m ai2d_pipeline.cli validate manifest.json`
