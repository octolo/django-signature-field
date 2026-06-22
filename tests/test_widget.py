"""Tests for signature fonts and widget font selection."""

from __future__ import annotations

import base64

from django import forms
from django.test import SimpleTestCase, override_settings

from signature import (
    SignatureField,
    SignatureWidget,
    discover_signature_fonts,
    get_signature_fonts,
)
from signature.fields import parse_signature_data
from tests.app.models import SignedDocument

MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
MINIMAL_PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class SignatureFontTests(SimpleTestCase):
    def test_discover_signature_fonts_finds_packaged_fonts(self) -> None:
        fonts = discover_signature_fonts()
        assert len(fonts) >= 6
        ids = {font["id"] for font in fonts}
        assert "civil-manuscript" in ids
        assert "royalty-free" in ids

    def test_widget_uses_default_font_from_config(self) -> None:
        widget = SignatureWidget(default_font="royalty-free")
        config = widget.get_config()
        assert config["defaultFont"] == "royalty-free"
        assert len(config["fonts"]) >= 6

    def test_get_signature_fonts_uses_bundled_fonts_by_default(self) -> None:
        with override_settings(SIGNATURE_FONTS=None):
            assert get_signature_fonts() == discover_signature_fonts()

    def test_get_signature_fonts_includes_test_app_font(self) -> None:
        fonts = get_signature_fonts()
        ids = {font["id"] for font in fonts}
        assert "mr-de-haviland" in ids
        assert "civil-manuscript" in ids
        mr_font = next(font for font in fonts if font["id"] == "mr-de-haviland")
        assert mr_font["file"] == "fonts/MrDeHaviland-Regular.woff2"
        assert mr_font["label"] == "Mr De Haviland"

    @override_settings(
        SIGNATURE_FONTS=[
            {
                "id": "custom-script",
                "label": "Custom Script",
                "file": "signature/fonts/Royalty-Free.woff2",
            },
        ],
        SIGNATURE_DEFAULT_FONT="custom-script",
    )
    def test_get_signature_fonts_reads_settings(self) -> None:
        fonts = get_signature_fonts()
        assert len(fonts) == 1
        assert fonts[0]["id"] == "custom-script"
        assert fonts[0]["label"] == "Custom Script"
        assert fonts[0]["family"] == "SignatureCustomScript"

        widget = SignatureWidget()
        assert widget.resolve_default_font() == "custom-script"


class SignatureWidgetTests(SimpleTestCase):
    def test_media_includes_js_and_css(self) -> None:
        media = SignatureWidget().media
        assert "signature/js/signature_widget.js" in media._js
        assert "signature/css/signature_widget.css" in media._css["all"]

    def test_format_value_encodes_bytes(self) -> None:
        widget = SignatureWidget()
        assert widget.format_value(MINIMAL_PNG) == MINIMAL_PNG_DATA_URL

    @override_settings(
        INSTALLED_APPS=[
            "django.contrib.staticfiles",
            "signature.apps.SignatureConfig",
            "tests.app",
        ],
    )
    def test_render_includes_test_app_font(self) -> None:
        widget = SignatureWidget(default_font="mr-de-haviland")
        html = widget.render("signature", "", attrs={"id": "id_signature"})
        assert "SignatureMrDeHaviland" in html
        assert "fonts/MrDeHaviland-Regular.woff2" in html
        assert "&quot;defaultFont&quot;: &quot;mr-de-haviland&quot;" in html

    @override_settings(INSTALLED_APPS=["django.contrib.staticfiles", "signature.apps.SignatureConfig"])
    def test_render_includes_canvas_font_select_and_font_face(self) -> None:
        widget = SignatureWidget(signer_name="Jane Doe", default_font="civil-manuscript")
        html = widget.render("signature", MINIMAL_PNG_DATA_URL, attrs={"id": "id_signature"})
        assert "data-signature-widget" in html
        assert "data-signature-input" in html
        assert "data-sw-font-prev" in html
        assert "data-sw-font-next" in html
        assert "data-sw-font-label" in html
        assert "data-sw-text-edit" in html
        assert "&#9000;" in html
        assert "<canvas" in html
        assert MINIMAL_PNG_DATA_URL in html
        assert "@font-face" in html
        assert "SignatureCivilManuscript" in html
        assert "&quot;defaultFont&quot;: &quot;civil-manuscript&quot;" in html
        assert "&quot;allowRedraw&quot;: false" in html
        assert 'class="sw-sign"' not in html
        assert "data-sw-limit" not in html

    @override_settings(INSTALLED_APPS=["django.contrib.staticfiles", "signature.apps.SignatureConfig"])
    def test_render_initial_mode_is_square_and_limited(self) -> None:
        widget = SignatureWidget(initial_mode=True, max_chars=5)
        html = widget.render("initials", "", attrs={"id": "id_initials"})
        assert "is-initial-mode" in html
        assert "data-sw-text-edit" in html
        assert "&quot;initialMode&quot;: true" in html
        assert "&quot;maxChars&quot;: 5" in html
        assert "data-sw-limit" in html
        assert 'class="sw-limit-value">5</span>' in html


class SignatureFormTests(SimpleTestCase):
    def test_blob_field_uses_signature_widget(self) -> None:
        field = SignedDocument._meta.get_field("signature")
        form_field = field.formfield()
        assert isinstance(form_field.widget, SignatureWidget)

    def test_initials_field_uses_initial_mode_widget(self) -> None:
        field = SignedDocument._meta.get_field("initials")
        form_field = field.formfield()
        assert isinstance(form_field.widget, SignatureWidget)
        assert form_field.widget.initial_mode is True
        assert form_field.widget.max_chars == 5
        assert form_field.widget.text == "JD"
        assert form_field.widget.canvas_width == form_field.widget.canvas_height

    def test_form_accepts_data_url(self) -> None:
        class DocumentForm(forms.ModelForm):
            class Meta:
                model = SignedDocument
                fields = ["title", "signature"]

        form = DocumentForm(data={"title": "Test", "signature": MINIMAL_PNG_DATA_URL})
        assert form.is_valid(), form.errors
        assert parse_signature_data(form.cleaned_data["signature"]) == MINIMAL_PNG
