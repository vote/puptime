from django.contrib import admin
from django.urls import include, path

from uptime.urls import urlpatterns as uptime_urlpatterns

urlpatterns = [
    path("-/", include("django_alive.urls")),
    path("admin/", admin.site.urls),
    path("v1/", include("app.api_urls")),
] + uptime_urlpatterns
