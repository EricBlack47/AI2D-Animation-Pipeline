# demo-character

This folder hosts OSS-safe demonstration assets and references.

## Demo sequence

- `idle`: 8 frames (`idle_0001.png` ... `idle_0008.png`)
- `attack`: 10 frames (`attack_0001.png` ... `attack_0010.png`)
- `hurt`: 6 frames (`hurt_0001.png` ... `hurt_0006.png`)

Generation command:

```bash
python tools/generate_demo_assets.py --output examples/demo-character
```

Manifest example is provided at:
`../demo_character_manifest.example.json`
