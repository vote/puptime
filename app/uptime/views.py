import logging

from django.http import HttpResponse
from django.views.generic.detail import DetailView
from django_tables2 import SingleTableView

from .models import Check, Downtime, Site
from .tables import CheckTable, DowntimeTable, SiteTable

logger = logging.getLogger("uptime")


class SiteListView(SingleTableView):
    model = Site
    template_name = "uptime/sites.html"
    table_class = SiteTable
    queryset = Site.objects.filter(active=True)


class SiteDowntimeListView(SingleTableView):
    model = Downtime
    template_name = "uptime/site_downtimes.html"
    table_class = DowntimeTable

    def get_queryset(self):
        return Downtime.objects.filter(site_id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = Site.objects.get(pk=self.kwargs["pk"])
        return context


class SiteCheckListView(SingleTableView):
    model = Check
    template_name = "uptime/site_checks.html"
    table_class = CheckTable

    def get_queryset(self):
        return Check.objects.filter(site_id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = Site.objects.get(pk=self.kwargs["pk"])
        return context


class CheckView(DetailView):
    template_name = "uptime/check.html"
    model = Check

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.content and self.object.content.content:
            context["clean_content"] = self.object.content.content
        return context


class DowntimeListView(SingleTableView):
    model = Downtime
    template_name = "uptime/downtimes.html"
    table_class = DowntimeTable

    def get_queryset(self):
        return Downtime.objects.all()


def test_nonce_view(request, nonce):
    return HttpResponse(nonce)
