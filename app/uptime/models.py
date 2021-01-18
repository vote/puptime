import datetime

from django.db import models

from common import enums
from common.models import TimestampModel, UUIDModel


class Site(UUIDModel, TimestampModel):
    url = models.TextField(null=True)
    active = models.BooleanField(default=True)
    description = models.TextField(null=True)
    metadata = models.JSONField(null=True)  # type: ignore
    owner = models.ForeignKey(
        "auth.User", related_name="sites", on_delete=models.CASCADE
    )

    status = models.TextField(
        null=True, choices=[(tag.name, tag.value) for tag in enums.CheckStatus]
    )
    status_changed_at = models.DateTimeField(null=True)

    last_downtime = models.ForeignKey(
        "Downtime", null=True, on_delete=models.CASCADE, related_name="site_last"
    )

    uptime_day = models.FloatField(null=True)
    uptime_week = models.FloatField(null=True)
    uptime_month = models.FloatField(null=True)
    uptime_quarter = models.FloatField(null=True)

    last_went_blocked_check = models.ForeignKey(
        "Check", null=True, on_delete=models.CASCADE, related_name="site_blocked"
    )
    last_went_unblocked_check = models.ForeignKey(
        "Check", null=True, on_delete=models.CASCADE, related_name="site_unblocked"
    )

    class Meta:
        ordering = ["-modified_at"]

    def __str__(self):
        return f"Site {self.uuid} - {self.url}"

    def get_check_interval(self):
        if self.status in (enums.CheckStatus.BLOCKED, enums.CheckStatus.DOWN):
            # For DOWN and BLOCKED sites, do some exponential backoff (with min/max)
            last_checks = Check.objects.filter(site=self, ignore=False).order_by(
                "-created_at"
            )[0:2]
            if self.status == enums.CheckStatus.BLOCKED:
                # back off pretty aggressively
                MULT = 0.33
                MIN = 15 * 60
                MAX = 24 * 60 * 60
            else:
                MULT = 0.05
                MIN = 1 * 60
                MAX = 15 * 60
            if len(last_checks) == 2:
                duration = last_checks[0].created_at - last_checks[1].created_at
                return min(max(duration.total_seconds() * MULT, MIN), MAX)
            return MIN

        # default for up sites
        return 15 * 60

    def add_check(self, check):
        if check.status != self.status:
            if check.status == enums.CheckStatus.DOWN:
                self.last_downtime = Downtime.objects.create(
                    site=self,
                    first_down_check=check,
                    last_down_check=check,
                )
            elif check.status == enums.CheckStatus.UP and self.last_downtime:
                self.last_downtime.up_check = check
                self.last_downtime.save()
                self.last_downtime = None

            if self.status == enums.CheckStatus.BLOCKED:
                self.last_went_unblocked_check = check
            if check.status == enums.CheckStatus.BLOCKED:
                self.last_went_blocked_check = check

            self.status = check.status
            self.status_changed_at = check.created_at

        elif check.status == enums.CheckStatus.DOWN:
            # update the current downtime
            if self.last_downtime:
                self.last_downtime.last_down_check = check

    def rebuild_downtimes(self):
        # reset
        self.status = enums.CheckStatus.UP
        self.last_downtime = None
        Downtime.objects.filter(site=self).delete()

        # re-ingest checks
        for check in Check.objects.filter(site=self, ignore=False).order_by(
            "created_at"
        ):
            self.add_check(check)
        if self.last_downtime:
            self.last_downtime.save()
        self.calc_uptimes()
        self.save()

    def calc_uptimes(self):
        r = self.do_calc_uptime(
            [
                datetime.timedelta(days=1),
                datetime.timedelta(days=7),
                datetime.timedelta(days=30),
                datetime.timedelta(days=91),
                #            datetime.timedelta(years=1),
            ]
        )
        # print(r)
        (self.uptime_day, self.uptime_week, self.uptime_month, self.uptime_quarter) = r

    def do_calc_uptime(self, cutoffs):
        now = (
            Check.objects.filter(site=self, ignore=False)
            .order_by("-created_at")
            .first()
            .created_at
        )
        period = cutoffs.pop(0)
        cutoff = now - period
        total_down = 0
        r = []
        for downtime in Downtime.objects.filter(site=self).order_by("-created_at"):
            start = downtime.first_down_check.created_at
            end = (
                downtime.last_down_check.created_at if downtime.last_down_check else now
            )
            # print(f"downtime {start} to {end}")

            # complete period(s) ending after this downtime
            while cutoff >= end:
                # print(f" period {period} cutoff {cutoff} fully after")
                r.append(1.0 - total_down / period.total_seconds())
                if not cutoffs:
                    return r
                period = cutoffs.pop(0)
                cutoff = now - period

            # complete period(s) we overlap with
            while cutoff >= start:
                # print(f" period {period} cutoff {cutoff} partially after")
                period_down = total_down + (end - cutoff).total_seconds()
                r.append(1.0 - period_down / period.total_seconds())
                if not cutoffs:
                    return r
                period = cutoffs.pop(0)
                cutoff = now - period

            # this downtime is now entirely within the current period
            total_down += (end - start).total_seconds()
            # print(f" total down now {total_down}")

        # we assume site was "up" in pre-history
        while True:
            r.append(1.0 - total_down / period.total_seconds())
            if not cutoffs:
                return r
            period = cutoffs.pop(0)
            cutoff = now - period


class Check(UUIDModel, TimestampModel):
    site = models.ForeignKey("Site", null=True, on_delete=models.CASCADE)
    status = models.TextField(
        null=True, choices=[(tag.name, tag.value) for tag in enums.CheckStatus]
    )
    up = models.BooleanField(null=True)
    blocked = models.BooleanField(null=True)
    ignore = models.BooleanField(null=True)
    load_time = models.FloatField(null=True)
    error = models.TextField(null=True)
    proxy = models.ForeignKey("Proxy", null=True, on_delete=models.CASCADE)
    content = models.ForeignKey("Content", null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created_at"]


class Content(UUIDModel, TimestampModel):
    title = models.TextField(null=True)
    content = models.TextField(null=True)
    snapshot_url = models.TextField(null=True)


class Downtime(UUIDModel, TimestampModel):
    site = models.ForeignKey("Site", null=True, on_delete=models.CASCADE)
    first_down_check = models.ForeignKey(
        "Check", on_delete=models.CASCADE, related_name="downtime_first"
    )
    last_down_check = models.ForeignKey(
        "Check", null=True, on_delete=models.CASCADE, related_name="downtime_last"
    )
    up_check = models.ForeignKey(
        "Check", null=True, on_delete=models.CASCADE, related_name="downtime_up"
    )

    def duration(self):
        return up_check.created_at - down_check.created_at

    class Meta:
        ordering = ["-created_at"]


class Proxy(UUIDModel, TimestampModel):
    source = models.TextField(null=True)
    address = models.TextField(null=True)
    description = models.TextField(null=True)
    status = models.TextField(
        null=True, choices=[(tag.name, tag.value) for tag in enums.ProxyStatus]
    )
    failure_count = models.IntegerField(null=True)
    last_used = models.DateTimeField(null=True)
    metadata = models.JSONField(null=True)  # type: ignore

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Proxy {self.uuid} - {self.address} {self.status}"
