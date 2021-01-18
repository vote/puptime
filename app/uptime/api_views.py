import logging

from rest_framework import generics, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from common import enums

from .models import Check, Downtime, Proxy, Site
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    CheckSerializer,
    DowntimeSerializer,
    ProxySerializer,
    SiteSerializer,
)

logger = logging.getLogger("uptime")


class PaginationStyle(LimitOffsetPagination):
    default_limit = 100


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    pagination_class = PaginationStyle
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        for k in self.request.query_params.keys():
            if k in [f.name for f in Site._meta.fields]:
                qs = qs.filter(**{k: self.request.query_params.get(k) or None})
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SiteMineViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    pagination_class = PaginationStyle
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CheckViewSet(viewsets.ModelViewSet):
    queryset = Check.objects.all()
    serializer_class = CheckSerializer
    pagination_class = PaginationStyle
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]


class DowntimeViewSet(viewsets.ModelViewSet):
    queryset = Downtime.objects.all()
    serializer_class = DowntimeSerializer
    pagination_class = PaginationStyle
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        for k in self.request.query_params.keys():
            if k in [f.name for f in Downtime._meta.fields]:
                qs = qs.filter(**{k: self.request.query_params.get(k) or None})
        return qs


# nested site views
class SiteChecksList(generics.ListAPIView):
    serializer_class = CheckSerializer
    pagination_class = PaginationStyle
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Check.objects.filter(site_id=self.kwargs["pk"])


class SiteDowntimeList(generics.ListAPIView):
    serializer_class = DowntimeSerializer
    pagination_class = PaginationStyle
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]


# filtered site list views
class SiteDownList(generics.ListAPIView):
    queryset = Site.objects.filter(status=enums.CheckStatus.DOWN)
    serializer_class = SiteSerializer
    pagination_class = PaginationStyle
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]


class SiteBlockedList(generics.ListAPIView):
    queryset = Site.objects.filter(status=enums.CheckStatus.BLOCKED)
    serializer_class = SiteSerializer
    pagination_class = PaginationStyle
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]


# require API key for these views
class ProxyViewSet(viewsets.ModelViewSet):
    queryset = Proxy.objects.all()
    serializer_class = ProxySerializer
    pagination_class = PaginationStyle
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
