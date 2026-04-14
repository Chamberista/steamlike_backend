from django.contrib import admin
from django.urls import path
from library.views import health, register, entries, entries_detail

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/register/", register, name="register"),  # ← NUEVA
    path("api/library/entries/", entries, name="entries"),  # GET y POST
    path("api/library/entries/<int:entry_id>/", entries_detail, name="entries_detail"),  # GET y PATCH
]
