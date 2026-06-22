from django import forms
from django.contrib import admin

from signature import SignatureAdminMixin, SignatureModelForm, SignatureWidget, apply_signature_staff_access, signature_user_is_staff
from signature.widgets import resolve_image_download_url

from .demo_utils import DEFAULT_INITIALS_SIZE, DEFAULT_SIGNATURE_SIZE
from .forms import PLAYGROUND_FIELDS, WIDGET_DEFAULTS
from .models import SignedDocument, SignedDocumentNoRedraw


def configure_signature_widgets(form: forms.ModelForm) -> None:
    signature_width, signature_height = DEFAULT_SIGNATURE_SIZE
    initials_width, initials_height = DEFAULT_INITIALS_SIZE
    staff = signature_user_is_staff(getattr(form, "signature_user", None))
    instance = getattr(form, "instance", None)

    widget_settings = {
        "signature": {
            **WIDGET_DEFAULTS,
            "canvas_width": signature_width,
            "canvas_height": signature_height,
        },
        "signature_image": {
            **WIDGET_DEFAULTS,
            "canvas_width": signature_width,
            "canvas_height": signature_height,
        },
        "initials": {
            "default_font": "civil-manuscript",
            "initial_mode": True,
            "max_chars": 5,
            "text": "JD",
            "add_timestamp": False,
            "canvas_width": initials_width,
            "canvas_height": initials_height,
        },
        "initials_image": {
            "default_font": "royalty-free",
            "initial_mode": True,
            "max_chars": 5,
            "text": "JD",
            "add_timestamp": False,
            "canvas_width": initials_width,
            "canvas_height": initials_height,
        },
    }

    for name, settings in widget_settings.items():
        model_field = form._meta.model._meta.get_field(name)
        download_url = ""
        if (
            staff
            and model_field.field_type == "image"
            and instance is not None
            and instance.pk
        ):
            download_url = resolve_image_download_url(getattr(instance, name, None))
        form.fields[name].widget = SignatureWidget(
            allow_redraw=model_field.allow_redraw,
            field_type=model_field.field_type,
            manage=staff,
            staff_mode=staff,
            download_url=download_url,
            **settings,
        )


class SignedDocumentAdminForm(SignatureModelForm):
    class Meta:
        model = SignedDocument
        fields = PLAYGROUND_FIELDS

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        configure_signature_widgets(self)
        apply_signature_staff_access(self)


class SignedDocumentNoRedrawAdminForm(SignatureModelForm):
    class Meta:
        model = SignedDocumentNoRedraw
        fields = PLAYGROUND_FIELDS

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        configure_signature_widgets(self)
        apply_signature_staff_access(self)


class SignedDocumentAdmin(SignatureAdminMixin, admin.ModelAdmin):
    form = SignedDocumentAdminForm
    list_display = ("title", "id")
    search_fields = ("title",)
    fieldsets = (
        (None, {"fields": ("title",)}),
        ("Blob", {"fields": ("signature", "initials")}),
        ("Image", {"fields": ("signature_image", "initials_image")}),
    )


class SignedDocumentNoRedrawAdmin(SignatureAdminMixin, admin.ModelAdmin):
    form = SignedDocumentNoRedrawAdminForm
    list_display = ("title", "id")
    search_fields = ("title",)
    fieldsets = (
        (None, {"fields": ("title",)}),
        ("Blob", {"fields": ("signature", "initials")}),
        ("Image", {"fields": ("signature_image", "initials_image")}),
    )


admin.site.register(SignedDocument, SignedDocumentAdmin)
admin.site.register(SignedDocumentNoRedraw, SignedDocumentNoRedrawAdmin)
