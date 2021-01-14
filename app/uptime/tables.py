import django_tables2 as tables
from django.utils.html import format_html

from .models import Check, Downtime, Site


class URLColumn(tables.Column):
    def render(self, value):
        return format_html(f'<a href="{value}">{value}</a>')


class UptimeColumn(tables.Column):
    attrs = {
        "td": {
            "align": "right",
        }
    }

    def render(self, value):
        return "{:.2f}%".format(value * 100.0)


class CheckColumn(tables.Column):
    def render(self, value):
        return format_html(f'<a href="/checks/{value.uuid}/">{value.created_at}</a>')


class SiteTable(tables.Table):
    def render_description(self, value, record):
        return format_html(
            f'<a href="/sites/{record.uuid}/downtimes/">{record.description}</a>'
        )

    links = tables.Column(empty_values=())

    uptime_day = UptimeColumn()
    uptime_week = UptimeColumn()
    uptime_month = UptimeColumn()
    uptime_quarter = UptimeColumn()

    def render_links(self, record):
        return format_html(
            " | ".join(
                [
                    f'<a target="_blank" href="{record.url}">Visit</a>',
                    f'<a href="/sites/{record.uuid}/downtimes/">Downtimes</a>',
                    f'<a href="/sites/{record.uuid}/checks/">Checks</a>',
                ]
            )
        )

    class Meta:
        model = Site
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "description",
            "status",
            "status_changed_at",
            "uptime_day",
            "uptime_week",
            "uptime_month",
            "uptime_quarter",
        )


class DowntimeTable(tables.Table):
    duration = tables.Column(empty_values=())
    first_down_check = CheckColumn()
    last_down_check = CheckColumn()
    up_check = CheckColumn()

    def render_site(self, record):
        return format_html(
            f'<a href="/sites/{record.site.uuid}/downtimes/">{record.site.description}</a>'
        )

    def render_duration(self, record):
        duration = (
            record.last_down_check.created_at - record.first_down_check.created_at
        )
        return duration

    class Meta:
        model = Downtime
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "site",
            "duration",
            "first_down_check",
            "last_down_check",
            "up_check",
        )


class CheckTable(tables.Table):
    content = tables.Column(empty_values=())
    snapshot = tables.Column(empty_values=())

    def render_created_at(self, record, value):
        return format_html(f'<a href="/checks/{record.uuid}/">{value}</a>')

    def render_content(self, record):
        return format_html(f'<a href="{record.content_url}">Content</a>')

    def render_snapshot(self, record):
        return format_html(f'<a href="{record.snapshot_url}">Snapshot</a>')

    def render_proxy(self, value):
        return value.uuid

    class Meta:
        model = Check
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "created_at",
            "status",
            "ignore",
            "load_time",
            "proxy",
            "content",
            "snapshot",
        )
