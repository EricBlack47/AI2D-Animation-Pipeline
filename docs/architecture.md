# Architecture

## Scope

This repository contains a small, reusable Python pipeline for turning video
or PNG frame sequences into validated animation manifests. It is independent
of any game project, runtime repository, or external generation service.

The public boundary is deliberately narrow:

- frame discovery, ordering, and consistency checks
- optional alpha-processing interfaces
- external-tool resolution and FFmpeg preflight
- manifest generation and JSON Schema validation
- a command-line interface for the supported stages

## Components

```text
src/ai2d_pipeline/
  alpha.py                 optional alpha-processing interface
  cli.py                   command-line entry point
  frames.py                PNG discovery and frame validation
  io.py                    JSON and text I/O helpers
  manifest.py              manifest model and schema loading
  schemas/manifest.schema.json
  tool_resolver.py         FFmpeg/ffprobe resolution and preflight
  validation.py            shared validation issue types
  video.py                 video probing and frame extraction
```

`tools/generate_demo_assets.py` creates deterministic, synthetic PNGs for
local validation and CI. The generated files are not required source inputs
and are excluded from normal Git commits.

## Boundaries

- The package does not import a game project or require a game-specific file.
- External tools are selected by explicit CLI options, JSON configuration,
  process environment, PATH, and documented platform fallbacks.
- Runtime integration consumes the manifest contract; Unity binaries are not
  included in this repository.
- Project-specific adapters, credentials, private paths, commercial assets,
  and unrelated gameplay code remain outside the public boundary.

## Reproducibility

The minimum reproducible flow is:

1. install the package and development dependencies
2. generate synthetic demo frames
3. validate the frame directory
4. write and validate a manifest

CI runs this flow without private inputs or repository-local machine paths.
