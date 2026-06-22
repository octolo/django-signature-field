from django import forms

from signature import SignatureModelForm, SignatureWidget, apply_signature_staff_access, signature_user_is_staff
from signature.widgets import resolve_image_download_url

from .models import SignedDocument, SignedDocumentNoRedraw

WIDGET_DEFAULTS = {
    "signer_name": "Jane Doe",
    "default_font": "civil-manuscript",
    "add_timestamp": False,
}

PLAYGROUND_FIELDS = ["title", "signature", "initials", "signature_image", "initials_image"]


class PlaygroundForm(SignatureModelForm):
    """Compare blob/image signature and initials widgets side by side."""

    widget_allow_redraw = True

    class Meta:
        model = SignedDocument
        fields = PLAYGROUND_FIELDS

    def __init__(
        self,
        *args,
        signature_size: tuple[int, int],
        initials_size: tuple[int, int],
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        signature_width, signature_height = signature_size
        initials_width, initials_height = initials_size
        staff = signature_user_is_staff(getattr(self, "signature_user", None))
        widget_defaults = {
            **WIDGET_DEFAULTS,
            "manage": staff,
            "allow_redraw": self.widget_allow_redraw,
        }

        signature_field = self._meta.model._meta.get_field("signature")
        signature_image_field = self._meta.model._meta.get_field("signature_image")
        initials_field = self._meta.model._meta.get_field("initials")
        initials_image_field = self._meta.model._meta.get_field("initials_image")

        self.fields["signature"].widget = SignatureWidget(
            **widget_defaults,
            field_type=signature_field.field_type,
            staff_mode=staff,
            canvas_width=signature_width,
            canvas_height=signature_height,
        )
        self.fields["signature_image"].widget = SignatureWidget(
            **widget_defaults,
            field_type=signature_image_field.field_type,
            staff_mode=staff,
            download_url=resolve_image_download_url(getattr(self.instance, "signature_image", None))
            if staff and self.instance.pk
            else "",
            canvas_width=signature_width,
            canvas_height=signature_height,
        )
        self.fields["initials"].widget = SignatureWidget(
            default_font="civil-manuscript",
            initial_mode=True,
            max_chars=5,
            text="JD",
            manage=staff,
            allow_redraw=self.widget_allow_redraw,
            field_type=initials_field.field_type,
            staff_mode=staff,
            add_timestamp=False,
            canvas_width=initials_width,
            canvas_height=initials_height,
        )
        self.fields["initials_image"].widget = SignatureWidget(
            default_font="royalty-free",
            initial_mode=True,
            max_chars=5,
            text="JD",
            manage=staff,
            allow_redraw=self.widget_allow_redraw,
            field_type=initials_image_field.field_type,
            staff_mode=staff,
            download_url=resolve_image_download_url(getattr(self.instance, "initials_image", None))
            if staff and self.instance.pk
            else "",
            add_timestamp=False,
            canvas_width=initials_width,
            canvas_height=initials_height,
        )
        apply_signature_staff_access(self)


class PlaygroundNoRedrawForm(PlaygroundForm):
    widget_allow_redraw = False

    class Meta:
        model = SignedDocumentNoRedraw
        fields = PLAYGROUND_FIELDS
