"""Django Signature Field - Store canvas signatures as blob or image."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("django-signature-field")
except PackageNotFoundError:
    __version__ = "0.0.0"

from .admin import SignatureAdminMixin
from .fields import SignatureBlobField, SignatureField, SignatureImageField, field_has_signature_value
from .forms import (
    SignatureFormField,
    SignatureModelForm,
    apply_signature_staff_access,
    signature_user_is_staff,
)
from .fonts import (
    discover_signature_fonts,
    font_family_name,
    font_id,
    get_signature_default_font,
    get_signature_fonts,
)
from .widgets import SignatureWidget

__all__ = [
    "SignatureAdminMixin",
    "SignatureBlobField",
    "SignatureField",
    "SignatureFormField",
    "SignatureImageField",
    "SignatureModelForm",
    "SignatureWidget",
    "apply_signature_staff_access",
    "signature_user_is_staff",
    "discover_signature_fonts",
    "font_family_name",
    "font_id",
    "get_signature_default_font",
    "get_signature_fonts",
]
