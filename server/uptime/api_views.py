from rest_framework import generics, viewsets
from rest_framework.pagination import LimitOffsetPagination

from .models import Proxy, Site, SiteCheck, SiteDowntime
from .serializers import (
    ProxySerializer,
    SiteCheckSerializer,
    SiteDowntimeSerializer,
    SiteSerializer,
)

# from apikey.auth import ApiKeyAuthentication, ApiKeyRequired
# from apikey.models import ApiKey


class PaginationStyle(LimitOffsetPagination):
    default_limit = 100


"""    
class ApiKeyAllowsUptimeOrReadonly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Anybody can read
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # API key with allow_uptime required for making changes
        if (
            request.auth
            and isinstance(request.auth, ApiKey)
            and request.auth.allow_uptime
        ):
            return True
        return False
"""


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    pagination_class = PaginationStyle


#    authentication_classes = [ApiKeyAuthentication]
#    permission_classes = [ApiKeyAllowsUptimeOrReadonly]


class SiteCheckViewSet(viewsets.ModelViewSet):
    queryset = SiteCheck.objects.all()
    serializer_class = SiteCheckSerializer
    pagination_class = PaginationStyle


#    authentication_classes = [ApiKeyAuthentication]
#    permission_classes = [ApiKeyAllowsUptimeOrReadonly]


class SiteDowntimeViewSet(viewsets.ModelViewSet):
    queryset = SiteDowntime.objects.all()
    serializer_class = SiteDowntimeSerializer
    pagination_class = PaginationStyle


#    authentication_classes = [ApiKeyAuthentication]
#    permission_classes = [ApiKeyAllowsUptimeOrReadonly]


# nested site views
class SiteChecksList(generics.ListAPIView):
    serializer_class = SiteCheckSerializer
    pagination_class = PaginationStyle

    def get_queryset(self):
        return SiteCheck.objects.filter(site_id=self.kwargs["pk"])


class SiteDowntimeList(generics.ListAPIView):
    serializer_class = SiteDowntimeSerializer
    pagination_class = PaginationStyle


# filtered site list views
class SiteDownList(generics.ListAPIView):
    queryset = Site.objects.filter(state_up=False)
    serializer_class = SiteSerializer
    pagination_class = PaginationStyle


class SiteBlockedList(generics.ListAPIView):
    queryset = Site.objects.filter(blocked=True)
    serializer_class = SiteSerializer
    pagination_class = PaginationStyle


# require API key for these views
class ProxyViewSet(viewsets.ModelViewSet):
    queryset = Proxy.objects.all()
    serializer_class = ProxySerializer
    pagination_class = PaginationStyle


#    authentication_classes = [ApiKeyAuthentication]
#    permission_classes = [ApiKeyRequired]
