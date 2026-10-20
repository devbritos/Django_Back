from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="personal:functionary_list")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("personal/", include("personal.urls")),
    path("dashboard/", include("analytics.urls")),
    path("activities/", include("activities.urls")),
    path("agenda/", include("agenda.urls")),
]

handler403 = "config.views.permission_denied"
handler404 = "config.views.page_not_found"