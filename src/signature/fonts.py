from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from django.conf import settings

FONTS_DIR = Path(__file__).resolve().parent / "static" / "signature" / "fonts"


def font_id(name: str) -> str:
    """Build a stable id from a font file stem."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def font_family_name(name: str) -> str:
    """Build a CSS font-family name from a font label."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "", name)
    return f"Signature{slug}"


def discover_signature_fonts() -> list[dict[str, str]]:
    """Return available signature fonts from the static fonts directory."""
    if not FONTS_DIR.is_dir():
        return []

    fonts: list[dict[str, str]] = []
    for path in sorted(FONTS_DIR.glob("*.woff2")):
        label = path.stem.replace("-", " ")
        fonts.append(
            {
                "id": font_id(path.stem),
                "label": label,
                "file": f"signature/fonts/{path.name}",
                "family": font_family_name(label),
            }
        )
    return fonts


def normalize_font_entry(entry: dict[str, str]) -> dict[str, str]:
    """Fill in missing font metadata from a settings entry."""
    file_path = entry["file"]
    label = entry.get("label") or Path(file_path).stem.replace("-", " ")
    font_id_value = entry.get("id") or font_id(label)
    return {
        "id": font_id_value,
        "label": label,
        "file": file_path,
        "family": entry.get("family") or font_family_name(label),
    }


def get_signature_fonts() -> list[dict[str, str]]:
    """Return configured signature fonts, or the bundled defaults."""
    configured: Any = getattr(settings, "SIGNATURE_FONTS", None)
    if configured is None:
        return discover_signature_fonts()
    if not isinstance(configured, list):
        msg = "SIGNATURE_FONTS must be a list of font definitions."
        raise ValueError(msg)
    fonts: list[dict[str, str]] = []
    for index, entry in enumerate(configured):
        if not isinstance(entry, dict):
            msg = f"SIGNATURE_FONTS[{index}] must be a dict with at least a 'file' key."
            raise ValueError(msg)
        if "file" not in entry:
            msg = f"SIGNATURE_FONTS[{index}] must include a 'file' static path."
            raise ValueError(msg)
        fonts.append(normalize_font_entry(entry))
    return fonts


def get_signature_default_font() -> str | None:
    """Return the configured default font id, if any."""
    default_font = getattr(settings, "SIGNATURE_DEFAULT_FONT", None)
    if default_font in (None, ""):
        return None
    if not isinstance(default_font, str):
        msg = "SIGNATURE_DEFAULT_FONT must be a font id string."
        raise ValueError(msg)
    return default_font
