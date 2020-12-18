from rest_framework import generics, viewsets
from rest_framework.pagination import LimitOffsetPagination

from .models import Proxy, Site, Check, Downtime
from .serializers import (
    ProxySerializer,
    CheckSerializer,
    DowntimeSerializer,
    SiteSerializer,
)

import logging

logger = logging.getLogger()

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

    def get_queryset(self):
        qs = super().get_queryset()
        for k in self.request.query_params.keys():
            if k in [f.name for f in Site._meta.fields]:
                qs = qs.filter(**{k: self.request.query_params.get(k) or None})
        return qs

#    authentication_classes = [ApiKeyAuthentication]
#    permission_classes = [ApiKeyAllowsUptimeOrReadonly]


class CheckViewSet(viewsets.ModelViewSet):
    queryset = Check.objects.all()
    serializer_class = CheckSerializer
    pagination_class = PaginationStyle

#    authentication_classes = [ApiKeyAuthentication]
#    permission_classes = [ApiKeyAllowsUptimeOrReadonly]

    # refresh uptime values when a check is modified
    def perform_create(self, serializer):
        check = serializer.save()
        if check.site:
            check.site.calc_uptimes()

    def perform_update(self, serializer):
        check = serializer.save()
        if check.site:
            check.site.calc_uptimes()

    def perform_destroy(self, instance):
        instance.delete()
        if instance.site:
            instance.site.calc_uptimes()


class DowntimeViewSet(viewsets.ModelViewSet):
    queryset = Downtime.objects.all()
    serializer_class = DowntimeSerializer
    pagination_class = PaginationStyle

    def get_queryset(self):
        qs = super().get_queryset()
        for k in self.request.query_params.keys():
            if k in [f.name for f in Downtime._meta.fields]:
                qs = qs.filter(**{k: self.request.query_params.get(k) or None})
        return qs


#    authentication_classes = [ApiKeyAuthentication]
#    permission_classes = [ApiKeyAllowsUptimeOrReadonly]


# nested site views
class SiteChecksList(generics.ListAPIView):
    serializer_class = CheckSerializer
    pagination_class = PaginationStyle

    def get_queryset(self):
        return Check.objects.filter(site_id=self.kwargs["pk"])


class SiteDowntimeList(generics.ListAPIView):
    serializer_class = DowntimeSerializer
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
