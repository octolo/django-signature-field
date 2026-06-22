from __future__ import annotations

import base64
import json
from typing import Any

from django.forms.widgets import Widget
from django.templatetags.static import static

from .fields import (
    INITIAL_MODE_DEFAULT_CHARS,
    INITIAL_MODE_DEFAULT_TEXT,
    FieldType,
    field_has_signature_value,
    signature_redrawn_field_name,
    square_canvas_size,
)
from .fonts import get_signature_default_font, get_signature_fonts


def resolve_image_download_url(value: Any) -> str:
    if not field_has_signature_value(value) or isinstance(value, str):
        return ""
    try:
        url = value.url
    except (ValueError, AttributeError):
        return ""
    return url if isinstance(url, str) else ""


class SignatureWidget(Widget):
    """Canvas widget that stores a PNG data URL in a hidden input."""

    template_name = "signature/widget.html"

    class Media:
        css = {"all": ("signature/css/signature_widget.css",)}
        js = ("signature/js/signature_widget.js",)

    def __init__(
        self,
        attrs: dict[str, Any] | None = None,
        *,
        signer_name: str = "",
        text: str = "",
        line_width: float = 0.8,
        font_size: int = 48,
        fonts: list[dict[str, str]] | None = None,
        default_font: str | None = None,
        lock_as_signed: bool = False,
        manage: bool = False,
        allow_redraw: bool = False,
        add_timestamp: bool = True,
        canvas_min_width: int = 500,
        canvas_min_height: int = 200,
        canvas_width: int | None = None,
        canvas_height: int | None = None,
        initial_mode: bool = False,
        max_chars: int = INITIAL_MODE_DEFAULT_CHARS,
        field_type: FieldType = "blob",
        staff_mode: bool = False,
        download_url: str = "",
    ) -> None:
        self.signer_name = signer_name
        if initial_mode and not text and not signer_name:
            self.text = INITIAL_MODE_DEFAULT_TEXT
        else:
            self.text = text or signer_name
        self.line_width = line_width
        self.font_size = font_size
        self.fonts = fonts if fonts is not None else get_signature_fonts()
        if default_font is None:
            default_font = get_signature_default_font()
        self.default_font = default_font
        self.lock_as_signed = lock_as_signed
        self.manage = manage
        self.allow_redraw = allow_redraw
        self.add_timestamp = add_timestamp
        self.canvas_min_width = canvas_min_width
        self.canvas_min_height = canvas_min_height
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.initial_mode = initial_mode
        self.max_chars = max_chars if initial_mode else 0
        self.field_type = field_type
        self.staff_mode = staff_mode
        self.download_url = download_url
        if initial_mode and not canvas_width and not canvas_height:
            size = square_canvas_size(self.max_chars or INITIAL_MODE_DEFAULT_CHARS)
            self.canvas_width = size
            self.canvas_height = size
        super().__init__(attrs)

    def resolve_default_font(self) -> str | None:
        if not self.fonts:
            return None
        if self.default_font and any(font["id"] == self.default_font for font in self.fonts):
            return self.default_font
        return self.fonts[0]["id"]

    def get_fonts(self) -> list[dict[str, str]]:
        return [
            {
                **font,
                "url": static(font["file"]),
            }
            for font in self.fonts
        ]

    def get_config(self, *, locked: bool = False) -> dict[str, Any]:
        return {
            "signerName": self.signer_name,
            "text": self.text,
            "lineWidth": self.line_width,
            "fontSize": self.font_size,
            "fonts": self.get_fonts(),
            "defaultFont": self.resolve_default_font(),
            "lockAsSigned": self.lock_as_signed,
            "manage": False if locked else self.manage,
            "allowRedraw": False if locked else self.allow_redraw,
            "addTimestamp": self.add_timestamp,
            "canvasMinWidth": self.canvas_min_width,
            "canvasMinHeight": self.canvas_min_height,
            "canvasWidth": self.canvas_width,
            "canvasHeight": self.canvas_height,
            "initialMode": self.initial_mode,
            "maxChars": self.max_chars,
        }

    def format_value(self, value: Any) -> str:
        if value in (None, ""):
            return ""
        if isinstance(value, memoryview):
            value = bytes(value)
        if isinstance(value, (bytes, bytearray)):
            encoded = base64.b64encode(bytes(value)).decode("ascii")
            return f"data:image/png;base64,{encoded}"
        if isinstance(value, str):
            return value
        if hasattr(value, "read"):
            data = value.read()
            if isinstance(data, str):
                return data
            encoded = base64.b64encode(data).decode("ascii")
            return f"data:image/png;base64,{encoded}"
        return ""

    def get_context(self, name: str, value: Any, attrs: dict[str, Any] | None) -> dict[str, Any]:
        locked = bool(attrs and attrs.get("disabled"))
        download_url = self.download_url or resolve_image_download_url(value)
        context = super().get_context(name, self.format_value(value), attrs)
        widget = context["widget"]
        widget["config_json"] = json.dumps(self.get_config(locked=locked))
        widget["fonts"] = self.get_fonts()
        widget["has_value"] = bool(widget["value"])
        widget["initial_mode"] = self.initial_mode
        widget["max_chars"] = self.max_chars
        widget["show_download_link"] = (
            (self.staff_mode or self.manage)
            and self.field_type == "image"
            and bool(download_url)
        )
        widget["download_url"] = download_url
        widget["drawn_name"] = signature_redrawn_field_name(name)
        widget["drawn_value"] = "0"
        return context
