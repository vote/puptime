from django.contrib import admin

from . import models


@admin.register(models.Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("url", "active", "description", "owner")


@admin.register(models.Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ("site", "state_up", "blocked", "ignore")


@admin.register(models.Downtime)
class DowntimeAdmin(admin.ModelAdmin):
    list_display = ("site", "first_down_check", "last_down_check", "up_check")


@admin.register(models.Proxy)
class ProxyAdmin(admin.ModelAdmin):
    list_display = ("source", "address", "description", "status")
