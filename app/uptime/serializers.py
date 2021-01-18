from rest_framework import serializers

from .models import Check, Downtime, Proxy, Site


class CheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Check
        fields = [
            "uuid",
            "site",
            "up",
            "blocked",
            "ignore",
            "load_time",
            "error",
            "proxy",
            "created_at",
            "title",
            "content",
        ]


class SiteSerializer(serializers.ModelSerializer):
    # last_went_down_check = CheckSerializer(read_only=True)
    # last_went_up_check = CheckSerializer(read_only=True)

    class Meta:
        model = Site
        fields = [
            "uuid",
            "url",
            "active",
            "description",
            "metadata",
            "status",
            "status_changed_at",
            "last_downtime",
            "uptime_day",
            "uptime_week",
            "uptime_month",
            "uptime_quarter",
            "last_went_blocked_check",
            "last_went_unblocked_check",
        ]


class DowntimeSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField("get_duration")

    def get_duration(self, obj):
        if obj.up_check and obj.down_check:
            return (obj.up_check.created_at - obj.down_check.created_at).total_seconds()
        else:
            return None

    class Meta:
        model = Downtime
        fields = [
            "uuid",
            "site",
            "down_check",
            "up_check",
            "duration",
        ]


class ProxySerializer(serializers.ModelSerializer):
    class Meta:
        model = Proxy
        fields = [
            "uuid",
            "address",
            "description",
            "status",
            "failure_count",
            "last_used",
            "created_at",
            "modified_at",
        ]
