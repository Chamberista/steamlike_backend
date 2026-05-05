from django.contrib import admin
from django.urls import path
from library.views import health, register, login_view, logout_view, me, change_password, entries, entries_detail, catalog_search, catalog_by_ids, catalog_resolve, debug_email_test

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/register/", register, name="register"),
    path("api/auth/login/", login_view, name="login"),
     path("api/auth/logout/", logout_view, name="logout"),
    path("api/users/me/", me, name="me"),
    path("api/users/me/password/", change_password, name="change_password"),
    path("api/library/entries/", entries, name="entries"),
    path("api/library/entries/<int:entry_id>/", entries_detail, name="entries_detail"),
    path("api/catalog/search/", catalog_search, name="catalog_search"),
    path("api/catalog/games/", catalog_by_ids, name="catalog_by_ids"),
    path("api/catalog/resolve/", catalog_resolve, name="catalog_resolve"),
    path("api/debug/email/test/", debug_email_test, name="debug_email_test"),
]
