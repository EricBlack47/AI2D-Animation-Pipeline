# Contributing

Thanks for reviewing or improving this project.

## Development setup

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Workflow

- Keep changes minimal and scoped to the OSS API.
- Add/update tests for behavior changes.
- Run local smoke checks before opening PRs.
- Do not add proprietary assets or credentials.

## Release boundaries

- This repository intentionally avoids private game data and large binary media.
- Keep commits focused on OSS-safe code and docs.
