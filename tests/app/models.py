from django.db import models

from signature import SignatureField


class SignedDocument(models.Model):
    title = models.CharField(max_length=100)
    signature = SignatureField(allow_redraw=True)
    initials = SignatureField(initial_mode=5, allow_redraw=True)
    signature_image = SignatureField(
        field_type="image",
        upload_to="signatures/",
        allow_redraw=True,
    )
    initials_image = SignatureField(
        field_type="image",
        upload_to="signatures/initials/",
        initial_mode=5,
        allow_redraw=True,
    )

    class Meta:
        verbose_name = "Signed Document"
        verbose_name_plural = "Signed Documents"

    def __str__(self) -> str:
        return self.title


class SignedDocumentNoRedraw(models.Model):
    title = models.CharField(max_length=100)
    signature = SignatureField(allow_redraw=False)
    initials = SignatureField(initial_mode=5, allow_redraw=False)
    signature_image = SignatureField(
        field_type="image",
        upload_to="signatures/no-redraw/",
        allow_redraw=False,
    )
    initials_image = SignatureField(
        field_type="image",
        upload_to="signatures/no-redraw/initials/",
        initial_mode=5,
        allow_redraw=False,
    )

    class Meta:
        verbose_name = "Signed Document (no redraw)"
        verbose_name_plural = "Signed Documents (no redraw)"

    def __str__(self) -> str:
        return self.title
