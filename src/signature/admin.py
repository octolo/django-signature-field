from __future__ import annotations

from typing import Any


class SignatureAdminMixin:
    """Pass the current admin user to signature ModelForms."""

    def get_form(self, request: Any, obj: Any = None, **kwargs: Any) -> type:
        form_class = kwargs.get("form", self.form)

        class RequestForm(form_class):
            def __init__(self, *args: Any, **inner_kwargs: Any) -> None:
                inner_kwargs.setdefault("signature_user", request.user)
                super().__init__(*args, **inner_kwargs)

        kwargs["form"] = RequestForm
        return super().get_form(request, obj, **kwargs)
