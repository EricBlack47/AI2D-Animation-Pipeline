"""Generate simple synthetic demo frames for test and README usage."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def _frame(size, color, index, count, tag):
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    cx, cy = size[0] // 2, size[1] // 2
    r = 25 + (index % 5) * 2
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    draw.rectangle((0, 0, size[0] - 1, size[1] - 1), outline=(255, 255, 255, 80), width=1)
    draw.text((6, 6), f"{tag}:{index + 1}/{count}", fill=(255, 255, 255, 255))
    return image


def generate(output: Path, tag: str, count: int, size=(64, 64), color=(255, 140, 0, 255)):
    output = Path(output) / tag
    output.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        image = _frame(size, color, index, count, tag)
        image.save(output / f"{tag}_{index + 1:04d}.png", format="PNG")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Output base directory")
    parser.add_argument("--action-prefix", default="demo-character")
    args = parser.parse_args()
    base = Path(args.output)
    base.mkdir(parents=True, exist_ok=True)
    generate(base, "idle", 8, size=(64, 64), color=(120, 200, 255, 255))
    generate(base, "attack", 10, size=(64, 64), color=(255, 110, 110, 255))
    generate(base, "hurt", 6, size=(64, 64), color=(255, 220, 80, 255))
    print(f"Demo assets generated at {base}")


if __name__ == "__main__":
    main()
