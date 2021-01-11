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

    state_up = models.BooleanField(null=True)
    state_changed_at = models.DateTimeField(null=True)
    last_went_down_check = models.ForeignKey(
        "Check", null=True, on_delete=models.CASCADE, related_name="site_down"
    )
    last_went_up_check = models.ForeignKey(
        "Check", null=True, on_delete=models.CASCADE, related_name="site_up"
    )
    last_tweet_at = models.DateTimeField(null=True)

    uptime_day = models.FloatField(null=True)
    uptime_week = models.FloatField(null=True)
    uptime_month = models.FloatField(null=True)
    uptime_quarter = models.FloatField(null=True)

    blocked = models.BooleanField(null=True)
    blocked_changed_at = models.DateTimeField(null=True)
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

    @classmethod
    def get_sentinel_site(cls):
        sites = Site.objects.filter(description="sentinel")
        assert sites
        return sites[0]

    def calc_uptimes(self):
        r = self.do_calc_uptime(
            [3600 * 24, 3600 * 24 * 7, 3600 * 24 * 30, 3600 * 24 * 90]
        )
        # print(r)
        (self.uptime_day, self.uptime_week, self.uptime_month, self.uptime_quarter) = r

    def do_calc_uptime(self, cutoffs):
        now = None
        last = None
        total_up = 0
        total_down = 0
        cutoff = 0
        r = []
        for check in Check.objects.filter(site=self, ignore=False).order_by(
            "-created_at"
        ):
            ts = check.created_at.timestamp()
            if not last:
                now = ts
                cutoff = now - cutoffs.pop(0)
            else:
                assert cutoff < last
                while ts < cutoff:
                    tup = total_up
                    tdn = total_down
                    if check.state_up:
                        tup += last - cutoff
                    else:
                        tdn += last - cutoff
                    #                    print('cutoff %d  tup %d, tdn %d,  sum %d' % (cutoff, tup, tdn, tup+tdn))
                    assert tup + tdn == now - cutoff
                    r.append(float(tup) / float(tup + tdn))
                    if not cutoffs:
                        return r
                    cutoff = now - cutoffs.pop(0)
                if check.state_up:
                    total_up += last - ts
                else:
                    total_down += last - ts
            #                print('cutoff %s  tup %d, tdn %d' % (cutoff, total_up, total_down))
            last = ts

        # we assume up for pre-history
        assert cutoff < last
        while True:
            total_up += last - cutoff
            last = cutoff
            r.append(float(total_up) / float(total_up + total_down))
            if not cutoffs:
                return r
            cutoff = now - cutoffs.pop(0)


class Check(UUIDModel, TimestampModel):
    site = models.ForeignKey("Site", null=True, on_delete=models.CASCADE)
    state_up = models.BooleanField(null=True)
    blocked = models.BooleanField(null=True)
    ignore = models.BooleanField(null=True)
    load_time = models.FloatField(null=True)
    error = models.TextField(null=True)
    proxy = models.ForeignKey("Proxy", null=True, on_delete=models.CASCADE)
    title = models.TextField(null=True)
    content = models.TextField(null=True)
    snapshot_url = models.TextField(null=True)

    class Meta:
        ordering = ["-created_at"]


class Classifier(UUIDModel, TimestampModel):
    name = models.TextField(null=True)

    class Meta:
        ordering = ["-created_at"]


class ClassifierPattern(UUIDModel, TimestampModel):
    classifier = models.ForeignKey("Classifier", on_delete=models.CASCADE)
    pattern_type = models.TextField(
        choices=[(tag.name, tag.value) for tag in enums.ClassifierPatternType]
    )
    pattern = models.TextField()

    class Meta:
        ordering = ["created_at"]


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
