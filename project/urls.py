# project/urls.py

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),

    path("", include("example_app.urls")),

    # Uploaded files (fine for small sites, no nginx needed).
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns.insert(0, path("__reload__/", include("django_browser_reload.urls")))
