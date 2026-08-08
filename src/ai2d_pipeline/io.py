"""I/O helpers for JSON/Markdown/TOML-like payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def write_json(path: Path, payload: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.write_bytes(data)
    return path


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_markdown(path: Path, lines: Iterable[str]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(str(line) for line in lines).rstrip() + "\n"
    path.write_text(text, encoding="utf-8")
    return path
