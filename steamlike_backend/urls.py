from django.contrib import admin
from django.urls import path
from library.views import health, register, login_view, logout_view, me, change_password, entries, entries_detail

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/register/", register, name="register"),
    path("api/auth/login/", login_view, name="login"),
     path("api/auth/logout/", logout_view, name="logout"),
    path("api/users/me/", me, name="me"),
    path("api/users/me/password/", change_password, name="change_password"),
    path("api/library/entries/", entries, name="entries"),  # GET y POST
    path("api/library/entries/<int:entry_id>/", entries_detail, name="entries_detail"),  # GET y PATCH
]
