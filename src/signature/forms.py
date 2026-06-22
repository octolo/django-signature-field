from __future__ import annotations

from typing import Any

from django import forms

from .fields import field_has_signature_value, signature_redrawn_field_name
from .widgets import SignatureWidget, resolve_image_download_url


def signature_user_is_staff(user: Any) -> bool:
    if user is None:
        return False
    return bool(getattr(user, "is_active", False)) and (
        getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)
    )


def apply_signature_staff_access(form: forms.BaseForm) -> None:
    """Unlock locked signature fields and expose staff tools for staff users."""
    if not signature_user_is_staff(getattr(form, "signature_user", None)):
        return

    instance = getattr(form, "instance", None)
    for name, field in form.fields.items():
        if not isinstance(field, SignatureFormField):
            continue

        widget = field.widget
        if isinstance(widget, SignatureWidget):
            widget.staff_mode = True
            if (
                widget.field_type == "image"
                and instance is not None
                and instance.pk
            ):
                file_value = getattr(instance, name, None)
                download_url = resolve_image_download_url(file_value)
                if download_url:
                    widget.download_url = download_url

        if field.allow_redraw or not field.allow_staff_redraw:
            continue
        if instance is None or not instance.pk:
            continue
        if not field_has_signature_value(getattr(instance, name, None)):
            continue

        field._staff_redraw_active = True
        field.disabled = False
        if isinstance(widget, SignatureWidget):
            widget.allow_redraw = True
            widget.manage = True


class SignatureFormField(forms.CharField):
    """Form field wired from SignatureField; locks existing values when redraw is disabled."""

    def __init__(
        self,
        *args: Any,
        allow_redraw: bool = True,
        allow_staff_redraw: bool = True,
        **kwargs: Any,
    ) -> None:
        self.allow_redraw = allow_redraw
        self.allow_staff_redraw = allow_staff_redraw
        self._staff_redraw_active = False
        super().__init__(*args, **kwargs)

    def _should_lock(self, form: forms.BaseForm, field_name: str) -> bool:
        if self.allow_redraw or getattr(self, "_staff_redraw_active", False):
            return False
        instance = getattr(form, "instance", None)
        if instance is None or not instance.pk:
            return False
        return field_has_signature_value(getattr(instance, field_name, None))

    def get_bound_field(self, form: forms.BaseForm, field_name: str) -> forms.BoundField:
        if self._should_lock(form, field_name):
            self.disabled = True
        return super().get_bound_field(form, field_name)

    def has_changed(self, initial: Any, data: Any) -> bool:
        if (
            not self.allow_redraw
            and field_has_signature_value(initial)
            and not getattr(self, "_staff_redraw_active", False)
        ):
            return False
        return super().has_changed(initial, data)

    def bound_data(self, data: Any, initial: Any) -> Any:
        if (
            not self.allow_redraw
            and field_has_signature_value(initial)
            and not getattr(self, "_staff_redraw_active", False)
        ):
            return initial
        return super().bound_data(data, initial)

    def clean(self, value: Any) -> Any:
        value = super().clean(value)
        if getattr(self, "_staff_redraw_active", False) and value in (None, ""):
            return None
        return value


class SignatureModelForm(forms.ModelForm):
    """ModelForm that passes staff edits through locked signature fields on save."""

    signature_user = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "signature_user" in kwargs:
            self.signature_user = kwargs.pop("signature_user")
        super().__init__(*args, **kwargs)
        apply_signature_staff_access(self)

    def save(self, commit: bool = True) -> Any:
        self._mark_signature_staff_edits()
        self._mark_signature_redraws()
        return super().save(commit=commit)

    def _mark_signature_redraws(self) -> None:
        redrawn: set[str] = set()
        data = getattr(self, "data", None)
        if data is not None:
            for name, field in self.fields.items():
                if not isinstance(field, SignatureFormField):
                    continue
                if data.get(signature_redrawn_field_name(name)) == "1":
                    redrawn.add(name)
        if redrawn:
            self.instance._signature_redrawn = redrawn

    def _mark_signature_staff_edits(self) -> None:
        if not signature_user_is_staff(getattr(self, "signature_user", None)):
            return

        edited: set[str] = set()
        instance = self.instance
        for name, field in self.fields.items():
            if not isinstance(field, SignatureFormField):
                continue
            if field.allow_redraw or not field.allow_staff_redraw:
                continue
            if name not in self.changed_data:
                continue
            if not instance.pk:
                continue
            initial = self.initial.get(name)
            if field_has_signature_value(initial) or field_has_signature_value(
                self.cleaned_data.get(name)
            ):
                edited.add(name)

        if edited:
            instance._signature_staff_edited = edited
