from django.contrib import admin
from django.urls import path, include
from library.views import health
from library.views import entries

urlpatterns = [
    path("admin/", admin.site.urls),
    #path("api/library/", include("core.urls")),
    path("api/health/", health),
    path("api/library/entries/", entries)
]
