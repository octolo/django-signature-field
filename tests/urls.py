"""URL configuration for tests."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from tests.app.views import (
    demo_home,
    demo_playground,
    demo_playground_no_redraw,
    demo_standalone,
    document_edit,
    document_list,
    document_no_redraw_edit,
)

urlpatterns = [
    path("", demo_home, name="signature-home"),
    path("standalone/", demo_standalone, name="signature-standalone"),
    path("documents/", document_list, name="signature-documents"),
    path("documents/<int:pk>/edit/", document_edit, name="signature-document-edit"),
    path(
        "documents/locked/<int:pk>/edit/",
        document_no_redraw_edit,
        name="signature-document-no-redraw-edit",
    ),
    path("play/", demo_playground, name="signature-playground"),
    path("play/locked/", demo_playground_no_redraw, name="signature-playground-no-redraw"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
