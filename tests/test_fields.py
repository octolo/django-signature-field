"""Tests for SignatureField storage modes."""

from __future__ import annotations

import base64

import pytest
from django import forms
from django.core.files.storage import default_storage

from signature import SignatureField
from signature.fields import (
    INITIAL_MODE_DEFAULT_CHARS,
    SignatureBlobField,
    field_has_signature_value,
    normalize_initial_mode,
    parse_signature_data,
    signature_redrawn_field_name,
    square_canvas_size,
)
from signature.forms import SignatureFormField, SignatureModelForm
from signature.stamp import apply_signature_timestamp
from signature.widgets import SignatureWidget
from tests.app.models import SignedDocument, SignedDocumentNoRedraw

MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
MINIMAL_PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def test_signature_field_defaults_to_blob() -> None:
    field = SignatureField()
    assert field.field_type == "blob"
    assert isinstance(field, SignatureBlobField)
    assert field.initial_mode is False


def test_signature_field_image_mode() -> None:
    field = SignatureField(field_type="image", upload_to="uploads/signatures/")
    assert field.field_type == "image"
    assert field.upload_to == "uploads/signatures/"


def test_signature_field_image_mode_accepts_custom_storage() -> None:
    from django.core.files.storage import FileSystemStorage

    custom_storage = FileSystemStorage(location="/tmp/signature-field-test")
    field = SignatureField(
        field_type="image",
        upload_to="uploads/signatures/",
        storage=custom_storage,
    )
    assert field.storage is custom_storage


def test_signature_field_rejects_storage_for_blob_mode() -> None:
    from django.core.files.storage import FileSystemStorage

    custom_storage = FileSystemStorage(location="/tmp/signature-field-test")
    with pytest.raises(ValueError, match="storage is only supported"):
        SignatureField(field_type="blob", storage=custom_storage)


def test_deconstruct_includes_custom_storage() -> None:
    from django.core.files.storage import FileSystemStorage

    custom_storage = FileSystemStorage(location="/tmp/signature-field-deconstruct")
    field = SignatureField(
        field_type="image",
        upload_to="signatures/custom/",
        storage=custom_storage,
    )
    _name, path, _args, kwargs = field.deconstruct()
    assert path == "signature.fields.SignatureField"
    assert kwargs["field_type"] == "image"
    assert kwargs["upload_to"] == "signatures/custom/"
    assert kwargs["storage"] is custom_storage


def test_signature_field_initial_mode_true_uses_default_chars() -> None:
    field = SignatureField(initial_mode=True)
    assert field.initial_mode == INITIAL_MODE_DEFAULT_CHARS
    widget = field.formfield().widget
    assert isinstance(widget, SignatureWidget)
    assert widget.initial_mode is True
    assert widget.max_chars == INITIAL_MODE_DEFAULT_CHARS
    assert widget.canvas_width == widget.canvas_height


def test_signature_field_initial_mode_with_limit() -> None:
    field = SignatureField(initial_mode=5)
    assert field.initial_mode == 5
    widget = field.formfield().widget
    assert widget.max_chars == 5
    assert widget.canvas_width == square_canvas_size(5)
    assert widget.canvas_width >= 100


def test_square_canvas_size_never_below_minimum() -> None:
    assert square_canvas_size(1) == 100
    assert square_canvas_size(3) >= 100


def test_normalize_initial_mode_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="initial_mode must be"):
        normalize_initial_mode(0)  # type: ignore[arg-type]


def test_signature_field_allow_redraw_passes_to_widget() -> None:
    field = SignatureField(allow_redraw=True)
    widget = field.formfield().widget
    assert widget.allow_redraw is True
    assert widget.get_config()["allowRedraw"] is True


def test_signature_field_allow_redraw_false_is_default() -> None:
    field = SignatureField()
    widget = field.formfield().widget
    assert widget.allow_redraw is False


def test_deconstruct_includes_allow_redraw_when_true() -> None:
    field = SignatureField(allow_redraw=True)
    _name, _path, _args, kwargs = field.deconstruct()
    assert kwargs["allow_redraw"] is True


def test_signed_document_no_redraw_model_fields_disable_redraw() -> None:
    for field_name in ("signature", "initials", "signature_image", "initials_image"):
        field = SignedDocumentNoRedraw._meta.get_field(field_name)
        assert field.allow_redraw is False
        widget = field.formfield().widget
        assert widget.allow_redraw is False
        assert widget.get_config()["allowRedraw"] is False


def test_signature_form_field_ignores_changes_when_locked() -> None:
    field = SignatureFormField(allow_redraw=False)
    assert field.has_changed(MINIMAL_PNG_DATA_URL, "") is False
    assert field_has_signature_value(MINIMAL_PNG_DATA_URL) is True


@pytest.mark.django_db
def test_locked_blob_field_restores_original_value_on_save() -> None:
    document = SignedDocumentNoRedraw.objects.create(
        title="Locked",
        signature=MINIMAL_PNG_DATA_URL,
    )
    document.refresh_from_db()
    original = document.signature
    document.signature = MINIMAL_PNG_DATA_URL.replace("AAA", "AAB")
    document.save()
    document.refresh_from_db()
    assert document.signature == original


@pytest.mark.django_db
def test_signature_form_field_locks_bound_field_for_existing_value() -> None:
    from django import forms

    document = SignedDocumentNoRedraw.objects.create(
        title="Locked",
        signature=MINIMAL_PNG_DATA_URL,
    )

    class DocumentForm(forms.ModelForm):
        class Meta:
            model = SignedDocumentNoRedraw
            fields = ["title", "signature"]

    form = DocumentForm(instance=document)
    bound_field = form["signature"]
    assert isinstance(form.fields["signature"], SignatureFormField)
    assert form.fields["signature"].disabled is True
    assert "disabled" in bound_field.build_widget_attrs({})


@pytest.mark.django_db
def test_staff_user_can_unlock_locked_signature_field() -> None:
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    staff = user_model.objects.create_user(
        "staff",
        "staff@example.com",
        "staff",
        is_staff=True,
    )
    document = SignedDocumentNoRedraw.objects.create(
        title="Locked",
        signature=MINIMAL_PNG_DATA_URL,
    )

    class DocumentForm(SignatureModelForm):
        class Meta:
            model = SignedDocumentNoRedraw
            fields = ["title", "signature"]

    form = DocumentForm(instance=document, signature_user=staff)
    assert form.fields["signature"].disabled is False
    assert form.fields["signature"].widget.allow_redraw is True
    assert form.fields["signature"].widget.manage is True


@pytest.mark.django_db
def test_staff_user_can_clear_locked_signature_to_empty() -> None:
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    staff = user_model.objects.create_user(
        "staff-clear",
        "staff-clear@example.com",
        "staff-clear",
        is_staff=True,
    )
    document = SignedDocumentNoRedraw.objects.create(
        title="Locked",
        signature=MINIMAL_PNG_DATA_URL,
    )

    class DocumentForm(SignatureModelForm):
        class Meta:
            model = SignedDocumentNoRedraw
            fields = ["title", "signature"]

    form = DocumentForm(
        {"title": "Locked", "signature": ""},
        instance=document,
        signature_user=staff,
    )
    assert form.is_valid(), form.errors
    saved = form.save()
    saved.refresh_from_db()
    assert saved.signature is None


@pytest.mark.django_db
def test_staff_user_can_clear_redrawable_signature_to_empty() -> None:
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    staff = user_model.objects.create_user(
        "staff-redraw-clear",
        "staff-redraw-clear@example.com",
        "staff-redraw-clear",
        is_staff=True,
    )
    document = SignedDocument.objects.create(
        title="Redrawable",
        signature=MINIMAL_PNG_DATA_URL,
    )

    class DocumentForm(SignatureModelForm):
        class Meta:
            model = SignedDocument
            fields = ["title", "signature"]

    form = DocumentForm(instance=document, signature_user=staff)
    assert form.fields["signature"].widget.manage is True

    form = DocumentForm(
        {
            "title": "Redrawable",
            "signature": "",
            signature_redrawn_field_name("signature"): "1",
        },
        instance=document,
        signature_user=staff,
    )
    assert form.is_valid(), form.errors
    saved = form.save()
    saved.refresh_from_db()
    assert saved.signature is None


@pytest.mark.django_db
def test_staff_image_field_shows_download_link() -> None:
    from django.contrib.auth import get_user_model
    from django.core.files.uploadedfile import SimpleUploadedFile

    user_model = get_user_model()
    staff = user_model.objects.create_user(
        "staff-image",
        "staff-image@example.com",
        "staff-image",
        is_staff=True,
    )
    uploaded = SimpleUploadedFile("signature.png", MINIMAL_PNG, content_type="image/png")
    document = SignedDocument.objects.create(
        title="Image doc",
        signature_image=uploaded,
    )

    class DocumentForm(SignatureModelForm):
        class Meta:
            model = SignedDocument
            fields = ["signature_image"]

    form = DocumentForm(instance=document, signature_user=staff)
    html = form["signature_image"].as_widget()
    assert "sw-download" in html
    assert "Download image" in html
    assert document.signature_image.url in html


@pytest.mark.django_db
def test_staff_blob_field_does_not_show_download_link() -> None:
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    staff = user_model.objects.create_user(
        "staff-blob",
        "staff-blob@example.com",
        "staff-blob",
        is_staff=True,
    )
    document = SignedDocument.objects.create(
        title="Blob doc",
        signature=MINIMAL_PNG_DATA_URL,
    )

    class DocumentForm(SignatureModelForm):
        class Meta:
            model = SignedDocument
            fields = ["signature"]

    form = DocumentForm(instance=document, signature_user=staff)
    html = form["signature"].as_widget()
    assert "sw-download" not in html


def test_signature_field_rejects_unknown_type() -> None:
    with pytest.raises(ValueError, match="field_type must be one of"):
        SignatureField(field_type="invalid")  # type: ignore[arg-type]


def test_parse_signature_data_from_bytes_and_data_url() -> None:
    assert parse_signature_data(MINIMAL_PNG) == MINIMAL_PNG
    assert parse_signature_data(MINIMAL_PNG_DATA_URL) == MINIMAL_PNG
    assert parse_signature_data(base64.b64encode(MINIMAL_PNG).decode("ascii")) == MINIMAL_PNG
    assert parse_signature_data(None) is None
    assert parse_signature_data("") is None


def test_parse_signature_data_rejects_invalid_base64() -> None:
    with pytest.raises(ValueError, match="Invalid signature data"):
        parse_signature_data("not-valid-base64!!")


@pytest.mark.django_db
def test_blob_field_stores_binary_signature() -> None:
    document = SignedDocument.objects.create(title="Blob doc", signature=MINIMAL_PNG_DATA_URL)
    document.refresh_from_db()
    expected = apply_signature_timestamp(MINIMAL_PNG)
    assert document.signature == expected
    assert document.signature != MINIMAL_PNG


@pytest.mark.django_db
def test_blob_initials_field_stores_binary_signature_without_timestamp() -> None:
    document = SignedDocument.objects.create(title="Initials doc", initials=MINIMAL_PNG_DATA_URL)
    document.refresh_from_db()
    assert document.initials == MINIMAL_PNG


@pytest.mark.django_db
def test_image_field_stores_file_signature() -> None:
    document = SignedDocument.objects.create(
        title="Image doc",
        signature_image=MINIMAL_PNG_DATA_URL,
    )
    document.refresh_from_db()
    expected = apply_signature_timestamp(MINIMAL_PNG)
    assert document.signature_image
    assert document.signature_image.read() == expected
    assert default_storage.exists(document.signature_image.name)


@pytest.mark.django_db
def test_image_initials_field_stores_file_signature_without_timestamp() -> None:
    document = SignedDocument.objects.create(
        title="Image initials doc",
        initials_image=MINIMAL_PNG_DATA_URL,
    )
    document.refresh_from_db()
    assert document.initials_image
    assert document.initials_image.read() == MINIMAL_PNG
    assert default_storage.exists(document.initials_image.name)


@pytest.mark.django_db
def test_resaving_unchanged_signature_does_not_restamp() -> None:
    document = SignedDocument.objects.create(title="Blob doc", signature=MINIMAL_PNG_DATA_URL)
    document.refresh_from_db()
    original = document.signature
    document.title = "Blob doc updated"
    document.save()
    document.refresh_from_db()
    assert document.signature == original


@pytest.mark.django_db
def test_form_resave_without_redraw_preserves_signature_bytes() -> None:
    document = SignedDocument.objects.create(title="Blob doc", signature=MINIMAL_PNG_DATA_URL)
    document.refresh_from_db()
    original = document.signature

    class DocumentForm(SignatureModelForm):
        class Meta:
            model = SignedDocument
            fields = ["title", "signature"]

    form = DocumentForm(
        {
            "title": "Blob doc updated",
            "signature": MINIMAL_PNG_DATA_URL,
            signature_redrawn_field_name("signature"): "0",
        },
        instance=document,
    )
    assert form.is_valid(), form.errors
    form.save()
    document.refresh_from_db()
    assert document.signature == original


@pytest.mark.django_db
def test_form_redraw_applies_timestamp() -> None:
    document = SignedDocument.objects.create(title="Blob doc", signature=MINIMAL_PNG_DATA_URL)
    document.refresh_from_db()

    class DocumentForm(SignatureModelForm):
        class Meta:
            model = SignedDocument
            fields = ["title", "signature"]

    form = DocumentForm(
        {
            "title": "Blob doc",
            "signature": MINIMAL_PNG_DATA_URL,
            signature_redrawn_field_name("signature"): "1",
        },
        instance=document,
    )
    assert form.is_valid(), form.errors
    form.save()
    document.refresh_from_db()
    assert document.signature == apply_signature_timestamp(MINIMAL_PNG)


def test_signature_field_does_not_stamp_without_redraw_on_update() -> None:
    field = SignatureField()
    field.set_attributes_from_name("signature")
    instance = type("Instance", (), {"pk": 1, "_signature_redrawn": set()})()
    assert field._should_stamp_signature(MINIMAL_PNG, instance, add=False) is False
    assert field._should_stamp_signature(MINIMAL_PNG, instance, add=True) is True


def test_signature_field_add_timestamp_false_skips_stamp() -> None:
    field = SignatureField(add_timestamp=False)
    widget = field.formfield().widget
    assert widget.add_timestamp is False
    assert field._should_stamp_signature(MINIMAL_PNG, object(), add=True) is False


def test_deconstruct_uses_signature_field_entry_point() -> None:
    blob_field = SignatureField(field_type="blob")
    _name, path, _args, kwargs = blob_field.deconstruct()
    assert path == "signature.fields.SignatureField"
    assert kwargs["field_type"] == "blob"

    image_field = SignatureField(field_type="image", upload_to="signatures/custom/")
    _name, path, _args, kwargs = image_field.deconstruct()
    assert path == "signature.fields.SignatureField"
    assert kwargs["field_type"] == "image"
    assert kwargs["upload_to"] == "signatures/custom/"

    initials_field = SignatureField(initial_mode=5)
    _name, path, _args, kwargs = initials_field.deconstruct()
    assert kwargs["initial_mode"] == 5
