from django.conf.urls import url
from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path("sites/", views.SiteListView.as_view()),
    path("sites/<str:pk>/downtimes/", views.SiteDowntimeListView.as_view()),
    path("sites/<str:pk>/checks/", views.SiteCheckListView.as_view()),
    path("checks/<str:pk>/", views.CheckView.as_view()),
    path("downtimes/", views.DowntimeListView.as_view()),
    path("test/<str:nonce>/", views.test_nonce_view),
    url(r"^$", TemplateView.as_view(template_name="index.html"), name="home"),
]
