from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.utils.formats import date_format
from django.utils.timezone import is_aware, localtime, make_aware, now


def format_signature_timestamp(when: datetime | None = None) -> str:
    """Return the label drawn in the bottom-right corner of stamped signatures."""
    when = when or now()
    if not is_aware(when):
        when = make_aware(when)
    return f"Signed: {date_format(localtime(when), 'SHORT_DATETIME_FORMAT')}"


def apply_signature_timestamp(png_bytes: bytes, when: datetime | None = None) -> bytes:
    """Draw a signing date in the bottom-right corner of a PNG image."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        msg = "Pillow is required to stamp signature dates. Install it with: pip install Pillow"
        raise ImproperlyConfigured(msg) from exc

    label = format_signature_timestamp(when)
    with Image.open(BytesIO(png_bytes)) as image:
        rgba = image.convert("RGBA")
        draw = ImageDraw.Draw(rgba)
        font = _load_timestamp_font()
        draw.text(
            (rgba.width - 10, rgba.height - 10),
            label,
            fill="black",
            font=font,
            anchor="rb",
        )
        output = BytesIO()
        rgba.save(output, format="PNG")
        return output.getvalue()


def _load_timestamp_font() -> Any:
    from PIL import ImageFont

    try:
        return ImageFont.truetype("DejaVuSans.ttf", 12)
    except OSError:
        return ImageFont.load_default()
