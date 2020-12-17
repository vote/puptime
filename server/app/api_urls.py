from django.urls import include, path

app_name = "api"
urlpatterns = [
    path("uptime/", include("uptime.api_urls")),
]
