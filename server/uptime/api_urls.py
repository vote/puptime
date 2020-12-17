from django.urls import path
from rest_framework.routers import DefaultRouter

from . import api_views

router = DefaultRouter()
router.register(r"sites", api_views.SiteViewSet, basename="site")
router.register(r"checks", api_views.SiteCheckViewSet, basename="check")
router.register(r"downtimes", api_views.SiteDowntimeViewSet, basename="downtime")
router.register(r"proxies", api_views.ProxyViewSet, basename="proxy")

urlpatterns = router.urls + [
    path("sites-down/", api_views.SiteDownList.as_view()),
    path("sites-blocked/", api_views.SiteBlockedList.as_view()),
    path("sites/<str:pk>/checks/", api_views.SiteChecksList.as_view()),
    path("sites/<str:pk>/downtime/", api_views.SiteDowntimeList.as_view()),
]
