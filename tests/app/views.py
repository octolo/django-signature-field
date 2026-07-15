from __future__ import annotations

import base64
from typing import Any

from django.db import models
from django.shortcuts import get_object_or_404, render

from .demo_utils import (
    DEFAULT_INITIALS_SIZE,
    DEFAULT_SIGNATURE_SIZE,
    DEMO_PRESETS,
    parse_initials_size,
    parse_size,
    size_param,
)
from .forms import PlaygroundForm, PlaygroundNoRedrawForm
from .models import SignedDocument, SignedDocumentNoRedraw

PREVIEW_FIELDS = ("signature", "initials", "signature_image", "initials_image")

DOCUMENT_SECTIONS = (
    {
        "label": "Allow redraw",
        "model": SignedDocument,
        "form_class": PlaygroundForm,
        "edit_url_name": "signature-document-edit",
    },
    {
        "label": "No redraw",
        "model": SignedDocumentNoRedraw,
        "form_class": PlaygroundNoRedrawForm,
        "edit_url_name": "signature-document-no-redraw-edit",
    },
)


def _document_previews(document: models.Model) -> dict[str, str]:
    previews: dict[str, str] = {}
    for name in ("signature", "initials"):
        value = getattr(document, name)
        if value:
            encoded = base64.b64encode(bytes(value)).decode("ascii")
            previews[name] = f"data:image/png;base64,{encoded}"
    for name in ("signature_image", "initials_image"):
        field_file = getattr(document, name)
        if field_file:
            previews[name] = field_file.url
    return previews


def document_list(request):
    sections = []
    for section in DOCUMENT_SECTIONS:
        items = []
        for document in section["model"].objects.order_by("-pk"):
            previews = _document_previews(document)
            items.append(
                {
                    "document": document,
                    "fields": [
                        {"name": name, "url": previews.get(name)}
                        for name in PREVIEW_FIELDS
                    ],
                    "edit_url_name": section["edit_url_name"],
                }
            )
        sections.append({**section, "items": items})
    return render(request, "tests/document_list.html", {"sections": sections})


def _form_previews(form) -> dict[str, str]:
    previews: dict[str, str] = {}
    for name in PREVIEW_FIELDS:
        value = form.cleaned_data.get(name)
        if not value:
            continue
        if hasattr(value, "read"):
            value.open("rb")
            encoded = base64.b64encode(value.read()).decode("ascii")
            previews[name] = f"data:image/png;base64,{encoded}"
        elif isinstance(value, (bytes, bytearray, memoryview)):
            encoded = base64.b64encode(bytes(value)).decode("ascii")
            previews[name] = f"data:image/png;base64,{encoded}"
        elif isinstance(value, str) and value.startswith("data:"):
            previews[name] = value
    return previews


def _playground_context(
    *,
    form,
    saved: bool,
    instance: models.Model | None,
    previews: dict[str, str],
    signature_size: tuple[int, int],
    initials_size: tuple[int, int],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = {
        "form": form,
        "saved": saved,
        "instance": instance,
        "previews": previews,
        "signature_size": signature_size,
        "initials_size": initials_size,
        "signature_param": size_param(signature_size),
        "initials_param": size_param(initials_size),
    }
    if extra:
        context.update(extra)
    return context


def _handle_playground(
    request,
    *,
    form_class: type[PlaygroundForm],
    template_name: str,
    extra: dict[str, Any] | None = None,
):
    signature_size = parse_size(
        request.GET.get("signature"),
        DEFAULT_SIGNATURE_SIZE,
    )
    initials_size = parse_initials_size(
        request.GET.get("initials"),
        DEFAULT_INITIALS_SIZE,
    )
    saved = False
    instance = None
    previews: dict[str, str] = {}

    if request.method == "POST":
        form = form_class(
            request.POST,
            signature_size=signature_size,
            initials_size=initials_size,
            signature_user=request.user,
        )
        if form.is_valid():
            instance = form.save()
            saved = True
            previews = _form_previews(form)
    else:
        form = form_class(
            signature_size=signature_size,
            initials_size=initials_size,
            signature_user=request.user,
        )

    return render(
        request,
        template_name,
        _playground_context(
            form=form,
            saved=saved,
            instance=instance,
            previews=previews,
            signature_size=signature_size,
            initials_size=initials_size,
            extra=extra,
        ),
    )


def _handle_document_edit(
    request,
    pk: int,
    *,
    model: type[models.Model],
    form_class: type[PlaygroundForm],
    documents_url_name: str,
):
    document = get_object_or_404(model, pk=pk)
    signature_size = parse_size(
        request.GET.get("signature"),
        DEFAULT_SIGNATURE_SIZE,
    )
    initials_size = parse_initials_size(
        request.GET.get("initials"),
        DEFAULT_INITIALS_SIZE,
    )
    saved = False
    previews: dict[str, str] = {}

    if request.method == "POST":
        form = form_class(
            request.POST,
            instance=document,
            signature_size=signature_size,
            initials_size=initials_size,
            signature_user=request.user,
        )
        if form.is_valid():
            document = form.save()
            saved = True
            previews = _form_previews(form)
    else:
        form = form_class(
            instance=document,
            signature_size=signature_size,
            initials_size=initials_size,
            signature_user=request.user,
        )

    return render(
        request,
        "tests/document_edit.html",
        {
            "form": form,
            "document": document,
            "saved": saved,
            "previews": previews,
            "signature_size": signature_size,
            "initials_size": initials_size,
            "signature_param": size_param(signature_size),
            "initials_param": size_param(initials_size),
            "documents_url_name": documents_url_name,
        },
    )


def document_edit(request, pk: int):
    return _handle_document_edit(
        request,
        pk,
        model=SignedDocument,
        form_class=PlaygroundForm,
        documents_url_name="signature-documents",
    )


def document_no_redraw_edit(request, pk: int):
    return _handle_document_edit(
        request,
        pk,
        model=SignedDocumentNoRedraw,
        form_class=PlaygroundNoRedrawForm,
        documents_url_name="signature-documents",
    )


def demo_standalone(request):
    """Render the widget with no model, form, or backend data.

    Proves the field can be built purely client-side from a config object,
    which is what enables reuse outside Django. Sizes come from the URL only
    so the template can forward them to the JS config.
    """
    signature_size = parse_size(request.GET.get("signature"), DEFAULT_SIGNATURE_SIZE)
    initials_size = parse_initials_size(request.GET.get("initials"), DEFAULT_INITIALS_SIZE)
    return render(
        request,
        "tests/standalone.html",
        {
            "signature_width": signature_size[0],
            "signature_height": signature_size[1],
            "initials_width": initials_size[0],
            "initials_height": initials_size[1],
            "signature_param": size_param(signature_size),
            "initials_param": size_param(initials_size),
        },
    )


def demo_home(request):
    presets = []
    for preset in DEMO_PRESETS:
        presets.append(
            {
                **preset,
                "url": (
                    f"/play/?signature={preset['signature']}&initials={preset['initials']}"
                ),
                "locked_url": (
                    f"/play/locked/?signature={preset['signature']}"
                    f"&initials={preset['initials']}"
                ),
                "standalone_url": (
                    f"/standalone/?signature={preset['signature']}"
                    f"&initials={preset['initials']}"
                ),
            }
        )
    return render(request, "tests/home.html", {"presets": presets})


def demo_playground(request):
    return _handle_playground(
        request,
        form_class=PlaygroundForm,
        template_name="tests/playground.html",
    )


def demo_playground_no_redraw(request):
    return _handle_playground(
        request,
        form_class=PlaygroundNoRedrawForm,
        template_name="tests/playground.html",
        extra={
            "playground_title": "Playground (no redraw)",
            "playground_back_url": "/",
            "documents_url_name": "signature-documents",
        },
    )
