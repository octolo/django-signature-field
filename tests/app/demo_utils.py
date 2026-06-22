from __future__ import annotations

import re

DEFAULT_SIGNATURE_SIZE = (320, 160)
DEFAULT_INITIALS_SIZE = (100, 100)
MIN_INITIALS_SIZE = (100, 100)
MAX_INITIALS_SIZE = 180
INITIALS_SIGNATURE_WIDTH_RATIO = 100 / 320

SIZE_RE = re.compile(r"^(\d+)x(\d+)$")

DEMO_PRESET_DEFINITIONS: list[dict[str, str]] = [
    {"label": "Small", "signature": "240x120"},
    {"label": "Standard", "signature": "320x160"},
    {"label": "Medium", "signature": "400x200"},
    {"label": "Large", "signature": "480x240"},
    {"label": "Wide", "signature": "520x240"},
]


def parse_size(value: str | None, default: tuple[int, int]) -> tuple[int, int]:
    """Parse a ``WIDTHxHEIGHT`` string into pixel dimensions."""
    if not value:
        return default
    match = SIZE_RE.match(value.strip().lower())
    if not match:
        return default
    width = int(match.group(1))
    height = int(match.group(2))
    if width < 40 or height < 40 or width > 1200 or height > 600:
        return default
    return width, height


def parse_initials_size(
    value: str | None,
    default: tuple[int, int] = DEFAULT_INITIALS_SIZE,
) -> tuple[int, int]:
    """Parse initials dimensions, never below ``MIN_INITIALS_SIZE``."""
    width, height = parse_size(value, default)
    return (
        max(width, MIN_INITIALS_SIZE[0]),
        max(height, MIN_INITIALS_SIZE[1]),
    )


def size_param(size: tuple[int, int]) -> str:
    return f"{size[0]}x{size[1]}"


def signature_area(signature: str) -> int:
    width, height = parse_size(signature, (0, 0))
    return width * height


def initials_size_for_signature(signature: str) -> str:
    """Scale initials with signature width, keeping a square canvas."""
    width, _height = parse_size(signature, DEFAULT_SIGNATURE_SIZE)
    size = round(width * INITIALS_SIGNATURE_WIDTH_RATIO)
    size = max(MIN_INITIALS_SIZE[0], min(MAX_INITIALS_SIZE, size))
    return size_param((size, size))


def build_demo_presets() -> list[dict[str, str]]:
    presets: list[dict[str, str]] = []
    for item in DEMO_PRESET_DEFINITIONS:
        presets.append(
            {
                "label": item["label"],
                "signature": item["signature"],
                "initials": initials_size_for_signature(item["signature"]),
            }
        )
    return sorted(presets, key=lambda preset: signature_area(preset["signature"]))


DEMO_PRESETS = build_demo_presets()
