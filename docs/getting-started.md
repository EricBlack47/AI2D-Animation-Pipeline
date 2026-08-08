# Getting Started

1. Install dependencies:
   `python -m pip install -e .`
2. Run `python -m ai2d_pipeline.cli doctor` to confirm required tools.
3. Generate demo assets:
   `python tools/generate_demo_assets.py --output examples/demo-character`
4. Extract frames from video:
   `python -m ai2d_pipeline.cli extract your_video.mp4 outputs/frames --fps source`
5. Validate:
   `python -m ai2d_pipeline.cli validate outputs/frames`
   - frame files in the same folder must follow one pattern like `prefix_0001.png`, all contiguous, same width
6. Create manifest:
   `python -m ai2d_pipeline.cli manifest outputs/frames --character demo-character --action idle --fps 32 --output outputs/frames/manifest.json`
