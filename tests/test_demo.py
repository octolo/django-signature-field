"""Tests for demo pages."""

import base64

import pytest
from django.test import Client, SimpleTestCase

from tests.app.models import SignedDocument, SignedDocumentNoRedraw

MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
MINIMAL_PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class DemoPageTests(SimpleTestCase):
    def test_home_page_lists_presets(self) -> None:
        response = Client().get("/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Signature field demos" in content
        assert "/play/?signature=320x160&amp;initials=100x100" in content
        assert "/play/locked/?signature=320x160&amp;initials=100x100" in content
        assert "Allow redraw" in content
        assert "No redraw" in content
        assert "Small" in content
        assert content.index("Small") < content.index("Wide")

    def test_playground_uses_url_sizes(self) -> None:
        response = Client().get("/play/?signature=320x200&initials=50x50")
        assert response.status_code == 200
        content = response.content.decode()
        assert "320x200" in content
        assert "100x100" in content
        assert "50x50" not in content
        assert content.count("data-signature-widget") == 4

    def test_playground_defaults_without_params(self) -> None:
        response = Client().get("/play/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "320x160" in content
        assert "100x100" in content

    def test_standalone_page_has_no_backend_widgets(self) -> None:
        response = Client().get("/standalone/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Signature without backend data" in content
        assert "SignatureField.create" in content
        assert "signature/js/signature_widget.js" in content
        assert "signature/css/signature_fonts.css" in content
        assert content.count("data-signature-widget") == 0

    def test_document_list_page(self) -> None:
        response = Client().get("/documents/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Signed documents" in content
        assert "Allow redraw" in content
        assert "No redraw" in content
        assert "No documents in this section yet." in content

    def test_playground_no_redraw_page(self) -> None:
        response = Client().get("/play/locked/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Playground (no redraw)" in content
        assert '"allowRedraw": false' in content
        assert content.count("data-signature-widget") == 4


@pytest.mark.django_db
def test_document_list_shows_edit_link() -> None:
    document = SignedDocument.objects.create(title="Contract A")
    response = Client().get("/documents/")
    content = response.content.decode()
    assert response.status_code == 200
    assert "Contract A" in content
    assert f'/documents/{document.pk}/edit/' in content


@pytest.mark.django_db
def test_document_edit_page() -> None:
    document = SignedDocument.objects.create(title="Contract B")
    response = Client().get(f"/documents/{document.pk}/edit/")
    content = response.content.decode()
    assert response.status_code == 200
    assert "Edit document" in content
    assert "Contract B" in content
    assert content.count("data-signature-widget") == 4


def test_document_edit_not_found() -> None:
    response = Client().get("/documents/999/edit/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_document_no_redraw_edit_page() -> None:
    document = SignedDocumentNoRedraw.objects.create(title="Locked contract")
    response = Client().get(f"/documents/locked/{document.pk}/edit/")
    content = response.content.decode()
    assert response.status_code == 200
    assert "Locked contract" in content
    assert '"allowRedraw": false' in content


@pytest.mark.django_db
def test_admin_lists_documents() -> None:
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    user_model.objects.create_superuser("admin", "admin@example.com", "admin")
    SignedDocument.objects.create(title="Admin doc")

    client = Client()
    client.login(username="admin", password="admin")

    changelist = client.get("/admin/app/signeddocument/")
    assert changelist.status_code == 200
    assert "Admin doc" in changelist.content.decode()

    add_page = client.get("/admin/app/signeddocument/add/")
    content = add_page.content.decode()
    assert add_page.status_code == 200
    assert content.count("data-signature-widget") == 4
    assert "&quot;manage&quot;: true" in content


@pytest.mark.django_db
def test_admin_no_redraw_change_form_disables_signed_fields_for_anonymous_user() -> None:
    document = SignedDocumentNoRedraw.objects.create(
        title="Locked doc",
        signature=MINIMAL_PNG_DATA_URL,
    )

    response = Client().get(f"/admin/app/signeddocumentnoredraw/{document.pk}/change/")
    content = response.content.decode()

    assert response.status_code == 302


@pytest.mark.django_db
def test_admin_no_redraw_change_form_unlocks_fields_for_staff() -> None:
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    user_model.objects.create_superuser("admin", "admin@example.com", "admin")
    document = SignedDocumentNoRedraw.objects.create(
        title="Locked doc",
        signature=MINIMAL_PNG_DATA_URL,
    )

    client = Client()
    client.login(username="admin", password="admin")
    response = client.get(f"/admin/app/signeddocumentnoredraw/{document.pk}/change/")
    content = response.content.decode()

    assert response.status_code == 200
    assert 'name="signature" disabled' not in content
    assert "&quot;allowRedraw&quot;: true" in content
    assert "&quot;manage&quot;: true" in content


@pytest.mark.django_db
def test_admin_change_form_shows_image_download_link() -> None:
    from django.contrib.auth import get_user_model
    from django.core.files.uploadedfile import SimpleUploadedFile

    user_model = get_user_model()
    user_model.objects.create_superuser("admin", "admin@example.com", "admin")
    uploaded = SimpleUploadedFile("signature.png", MINIMAL_PNG, content_type="image/png")
    document = SignedDocument.objects.create(
        title="Image admin doc",
        signature_image=uploaded,
    )

    client = Client()
    client.login(username="admin", password="admin")
    response = client.get(f"/admin/app/signeddocument/{document.pk}/change/")
    content = response.content.decode()

    assert response.status_code == 200
    assert "sw-download" in content
    assert "Download image" in content
    assert document.signature_image.url in content
