from __future__ import annotations

import base64
import binascii
import re
import uuid
from typing import Any, Literal

from django.core.files.base import ContentFile
from django.db import models

FieldType = Literal["blob", "image"]
InitialMode = bool | int

_DATA_URL_RE = re.compile(r"^data:[^;]+;base64,(?P<data>.+)$", re.DOTALL)
_FIELD_TYPES: tuple[FieldType, ...] = ("blob", "image")
INITIAL_MODE_DEFAULT_CHARS = 3
INITIAL_MODE_DEFAULT_TEXT = "JD"
INITIAL_MODE_MIN_CANVAS_SIZE = 100


def normalize_initial_mode(value: InitialMode) -> int | Literal[False]:
    """Return max characters for initials mode, or False when disabled."""
    if value is False:
        return False
    if value is True:
        return INITIAL_MODE_DEFAULT_CHARS
    if isinstance(value, int) and value > 0:
        return value
    msg = "initial_mode must be False, True, or a positive integer."
    raise ValueError(msg)


def square_canvas_size(max_chars: int) -> int:
    """Compute a square canvas size from the initials character limit."""
    return max(INITIAL_MODE_MIN_CANVAS_SIZE, min(180, 48 + max_chars * 22))


def parse_signature_data(value: Any) -> bytes | None:
    """Decode signature input from bytes, a data URL, or base64 text."""
    if value in (None, ""):
        return None
    if isinstance(value, memoryview):
        return bytes(value)
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if hasattr(value, "read"):
        data = value.read()
        if isinstance(data, str):
            return parse_signature_data(data)
        return bytes(data)

    if not isinstance(value, str):
        msg = f"Unsupported signature value type: {type(value).__name__}"
        raise ValueError(msg)

    raw_value = value.strip()
    match = _DATA_URL_RE.match(raw_value)
    if match:
        raw_value = match.group("data")

    try:
        return base64.b64decode(raw_value, validate=True)
    except (binascii.Error, ValueError) as exc:
        msg = "Invalid signature data: expected base64-encoded image content."
        raise ValueError(msg) from exc


def field_has_signature_value(value: Any) -> bool:
    if value in (None, ""):
        return False
    if hasattr(value, "name"):
        return bool(value.name)
    return True


def read_signature_bytes(value: Any) -> bytes | None:
    if value in (None, ""):
        return None
    if isinstance(value, memoryview):
        return bytes(value)
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if hasattr(value, "read"):
        data = value.read()
        if hasattr(value, "seek"):
            value.seek(0)
        if not data:
            return None
        return bytes(data) if isinstance(data, (bytes, bytearray)) else parse_signature_data(data)
    if isinstance(value, str):
        return parse_signature_data(value)
    return None


def signature_bytes_equal(left: Any, right: Any) -> bool:
    left_bytes = read_signature_bytes(left)
    right_bytes = read_signature_bytes(right)
    return left_bytes is not None and left_bytes == right_bytes


def signature_redrawn_field_name(field_name: str) -> str:
    """POST key used by the widget to report a user draw or redraw."""
    return f"{field_name}__drawn"


class SignatureFieldMixin:
    """Shared parsing logic and widget configuration for signature values."""

    field_type: FieldType
    initial_mode: int | Literal[False] = False
    _initial_mode_arg: InitialMode = False
    allow_redraw: bool = False
    _allow_redraw_arg: bool = False
    allow_staff_redraw: bool = True
    _allow_staff_redraw_arg: bool = True
    add_timestamp: bool = True
    _add_timestamp_arg: bool = True

    def _init_initial_mode(self, initial_mode: InitialMode) -> None:
        self._initial_mode_arg = initial_mode
        self.initial_mode = normalize_initial_mode(initial_mode)

    def _init_allow_redraw(self, allow_redraw: bool = False) -> None:
        self._allow_redraw_arg = allow_redraw
        self.allow_redraw = allow_redraw

    def _init_allow_staff_redraw(self, allow_staff_redraw: bool = True) -> None:
        self._allow_staff_redraw_arg = allow_staff_redraw
        self.allow_staff_redraw = allow_staff_redraw

    def _init_add_timestamp(self, add_timestamp: bool = True) -> None:
        self._add_timestamp_arg = add_timestamp
        self.add_timestamp = add_timestamp

    def get_widget_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "allow_redraw": self.allow_redraw,
            "field_type": self.field_type,
            "add_timestamp": self.add_timestamp and not self.initial_mode,
        }
        if self.initial_mode:
            size = square_canvas_size(self.initial_mode)
            kwargs.update(
                {
                    "initial_mode": True,
                    "max_chars": self.initial_mode,
                    "text": INITIAL_MODE_DEFAULT_TEXT,
                    "canvas_width": size,
                    "canvas_height": size,
                }
            )
        return kwargs

    def _initial_mode_deconstruct_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if self._initial_mode_arg is not False:
            kwargs["initial_mode"] = self._initial_mode_arg
        return kwargs

    def _allow_redraw_deconstruct_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if self._allow_redraw_arg:
            kwargs["allow_redraw"] = self._allow_redraw_arg
        return kwargs

    def _allow_staff_redraw_deconstruct_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if not self._allow_staff_redraw_arg:
            kwargs["allow_staff_redraw"] = self._allow_staff_redraw_arg
        return kwargs

    def _add_timestamp_deconstruct_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if not self._add_timestamp_arg:
            kwargs["add_timestamp"] = self._add_timestamp_arg
        return kwargs

    def _field_was_redrawn(self, model_instance: Any, add: bool) -> bool:
        if add:
            return True
        redrawn = getattr(model_instance, "_signature_redrawn", None) or set()
        return self.name in redrawn or self.attname in redrawn

    def _preserve_unchanged_signature(self, model_instance: Any, add: bool) -> Any | None:
        if self._field_was_redrawn(model_instance, add) or not model_instance.pk:
            return None
        old = (
            model_instance.__class__.objects.filter(pk=model_instance.pk)
            .values_list(self.attname, flat=True)
            .first()
        )
        if field_has_signature_value(old):
            return old
        return None

    def _should_stamp_signature(self, parsed: bytes, model_instance: Any, add: bool) -> bool:
        if not self.add_timestamp or self.initial_mode:
            return False
        return self._field_was_redrawn(model_instance, add)

    def _stamp_signature_bytes(self, parsed: bytes, model_instance: Any, add: bool) -> bytes:
        if not self._should_stamp_signature(parsed, model_instance, add):
            return parsed
        from .stamp import apply_signature_timestamp

        return apply_signature_timestamp(parsed)

    def _restore_locked_value(self, model_instance: Any, add: bool) -> Any | None:
        if add or self.allow_redraw or not model_instance.pk:
            return None
        edited = getattr(model_instance, "_signature_staff_edited", None) or set()
        if self.name in edited or self.attname in edited:
            return None
        return (
            model_instance.__class__.objects.filter(pk=model_instance.pk)
            .values_list(self.attname, flat=True)
            .first()
        )


class SignatureBlobField(SignatureFieldMixin, models.BinaryField):
    """Store a signature as raw binary data."""

    field_type: FieldType = "blob"

    def __init__(
        self,
        *args: Any,
        initial_mode: InitialMode = False,
        allow_redraw: bool = False,
        allow_staff_redraw: bool = True,
        add_timestamp: bool = True,
        **kwargs: Any,
    ) -> None:
        kwargs.pop("field_type", None)
        self._init_initial_mode(initial_mode)
        self._init_allow_redraw(allow_redraw)
        self._init_allow_staff_redraw(allow_staff_redraw)
        self._init_add_timestamp(add_timestamp)
        kwargs.setdefault("editable", True)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("null", True)
        super().__init__(*args, **kwargs)

    def to_python(self, value: Any) -> bytes | None:
        if value in (None, ""):
            return None
        return parse_signature_data(value)

    def get_prep_value(self, value: Any) -> bytes | None:
        if value in (None, ""):
            return None
        return parse_signature_data(value)

    def deconstruct(self) -> tuple[str, str, list[Any], dict[str, Any]]:
        name, _path, args, kwargs = super().deconstruct()
        kwargs["field_type"] = "blob"
        self._initial_mode_deconstruct_kwargs(kwargs)
        self._allow_redraw_deconstruct_kwargs(kwargs)
        self._allow_staff_redraw_deconstruct_kwargs(kwargs)
        self._add_timestamp_deconstruct_kwargs(kwargs)
        return name, "signature.fields.SignatureField", args, kwargs

    def formfield(self, **kwargs: Any) -> Any:
        from .forms import SignatureFormField
        from .widgets import SignatureWidget

        defaults: dict[str, Any] = {
            "form_class": SignatureFormField,
            "allow_redraw": self.allow_redraw,
            "allow_staff_redraw": self.allow_staff_redraw,
            "widget": SignatureWidget(**self.get_widget_kwargs()),
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def pre_save(self, model_instance: Any, add: bool) -> Any:
        edited = getattr(model_instance, "_signature_staff_edited", None) or set()
        if self.name in edited or self.attname in edited:
            value = getattr(model_instance, self.attname)
            if value in (None, ""):
                setattr(model_instance, self.attname, None)
                return super().pre_save(model_instance, add)

        unchanged = self._preserve_unchanged_signature(model_instance, add)
        if unchanged is not None:
            setattr(model_instance, self.attname, unchanged)
            return super().pre_save(model_instance, add)

        locked_value = self._restore_locked_value(model_instance, add)
        if locked_value is not None and field_has_signature_value(locked_value):
            setattr(model_instance, self.attname, locked_value)
            return super().pre_save(model_instance, add)

        value = getattr(model_instance, self.attname)
        parsed = read_signature_bytes(value)
        if parsed:
            stamped = self._stamp_signature_bytes(parsed, model_instance, add)
            if stamped is not parsed:
                setattr(model_instance, self.attname, stamped)
        return super().pre_save(model_instance, add)


class SignatureImageField(SignatureFieldMixin, models.ImageField):
    """Store a signature as an uploaded image file."""

    field_type: FieldType = "image"

    def __init__(
        self,
        *args: Any,
        upload_to: str = "signatures/",
        storage: Any = None,
        initial_mode: InitialMode = False,
        allow_redraw: bool = False,
        allow_staff_redraw: bool = True,
        add_timestamp: bool = True,
        **kwargs: Any,
    ) -> None:
        kwargs.pop("field_type", None)
        self._init_initial_mode(initial_mode)
        self._init_allow_redraw(allow_redraw)
        self._init_allow_staff_redraw(allow_staff_redraw)
        self._init_add_timestamp(add_timestamp)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("null", True)
        if storage is not None:
            kwargs["storage"] = storage
        super().__init__(*args, upload_to=upload_to, **kwargs)

    def _needs_decoding(self, value: Any) -> bool:
        if isinstance(value, str):
            return True
        name = getattr(value, "name", None)
        return isinstance(name, str) and name.startswith("data:")

    def to_python(self, value: Any) -> Any:
        if self._needs_decoding(value):
            raw = value if isinstance(value, str) else value.name
            parsed = parse_signature_data(raw)
            if parsed is None:
                return None
            return ContentFile(parsed, name=f"signature-{uuid.uuid4().hex}.png")
        return super().to_python(value)

    def pre_save(self, model_instance: Any, add: bool) -> Any:
        edited = getattr(model_instance, "_signature_staff_edited", None) or set()
        if self.name in edited or self.attname in edited:
            value = getattr(model_instance, self.attname)
            if value in (None, ""):
                setattr(model_instance, self.attname, None)
                return None

        locked_value = self._restore_locked_value(model_instance, add)
        if locked_value is not None and field_has_signature_value(locked_value):
            setattr(model_instance, self.attname, locked_value)
            return locked_value

        unchanged = self._preserve_unchanged_signature(model_instance, add)
        if unchanged is not None:
            setattr(model_instance, self.attname, unchanged)
            return unchanged

        value = getattr(model_instance, self.attname)
        if value in (None, ""):
            return value
        if self._needs_decoding(value):
            raw = value if isinstance(value, str) else value.name
            parsed = parse_signature_data(raw)
            if parsed is None:
                setattr(model_instance, self.attname, None)
                return None
            parsed = self._stamp_signature_bytes(parsed, model_instance, add)
            content = ContentFile(parsed, name=f"signature-{uuid.uuid4().hex}.png")
            setattr(model_instance, self.attname, content)
        else:
            parsed = read_signature_bytes(value)
            if parsed:
                stamped = self._stamp_signature_bytes(parsed, model_instance, add)
                if stamped is not parsed:
                    name = getattr(value, "name", f"signature-{uuid.uuid4().hex}.png")
                    setattr(model_instance, self.attname, ContentFile(stamped, name=name))
        return super().pre_save(model_instance, add)

    def formfield(self, **kwargs: Any) -> Any:
        from .forms import SignatureFormField
        from .widgets import SignatureWidget

        defaults: dict[str, Any] = {
            "form_class": SignatureFormField,
            "allow_redraw": self.allow_redraw,
            "allow_staff_redraw": self.allow_staff_redraw,
            "widget": SignatureWidget(**self.get_widget_kwargs()),
        }
        defaults.update(kwargs)
        return models.Field.formfield(self, **defaults)

    def deconstruct(self) -> tuple[str, str, list[Any], dict[str, Any]]:
        name, _path, args, kwargs = super().deconstruct()
        kwargs["field_type"] = "image"
        if kwargs.get("upload_to") == "signatures/":
            kwargs.pop("upload_to", None)
        self._initial_mode_deconstruct_kwargs(kwargs)
        self._allow_redraw_deconstruct_kwargs(kwargs)
        self._allow_staff_redraw_deconstruct_kwargs(kwargs)
        self._add_timestamp_deconstruct_kwargs(kwargs)
        return name, "signature.fields.SignatureField", args, kwargs


class SignatureField:
    """Factory for blob or image signature fields."""

    def __new__(
        cls,
        *args: Any,
        field_type: FieldType = "blob",
        upload_to: str = "signatures/",
        storage: Any = None,
        initial_mode: InitialMode = False,
        allow_redraw: bool = False,
        allow_staff_redraw: bool = True,
        add_timestamp: bool = True,
        **kwargs: Any,
    ) -> SignatureBlobField | SignatureImageField:
        if field_type not in _FIELD_TYPES:
            msg = f"field_type must be one of {_FIELD_TYPES}, got {field_type!r}."
            raise ValueError(msg)

        if storage is None:
            storage = kwargs.pop("storage", None)
        else:
            kwargs.pop("storage", None)

        if field_type == "blob":
            if storage is not None:
                msg = "storage is only supported when field_type='image'."
                raise ValueError(msg)
            return SignatureBlobField(
                *args,
                initial_mode=initial_mode,
                allow_redraw=allow_redraw,
                allow_staff_redraw=allow_staff_redraw,
                add_timestamp=add_timestamp,
                **kwargs,
            )
        return SignatureImageField(
            *args,
            upload_to=upload_to,
            storage=storage,
            initial_mode=initial_mode,
            allow_redraw=allow_redraw,
            allow_staff_redraw=allow_staff_redraw,
            add_timestamp=add_timestamp,
            **kwargs,
        )
