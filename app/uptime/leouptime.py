import sys
import datetime
import csv
import logging

import dateutil
import requests

from common import enums

from .check import classify_check
from .models import Check, Content, Proxy, Site

logger = logging.getLogger("uptime")

# https://stackoverflow.com/questions/15063936/csv-error-field-larger-than-field-limit-131072
csv.field_size_limit(sys.maxsize)


def import_proxies():
    with open("proxy.csv", "r") as f:
        r = csv.DictReader(f, delimiter=",")
        for i in r:
            print(i)
            try:
                proxy = Proxy.objects.get(uuid=i["uuid"])
            except:
                proxy = Proxy.objects.create(uuid=i["uuid"])
            proxy.source = "digitalocean"
            proxy.address = i["address"]
            proxy.description = i["description"]
            proxy.status = "down"
            if i["last_used"]:
                proxy.last_used = dateutil.parser.isoparse(i["last_used"])
            proxy.created_at = dateutil.parser.isoparse(i["created_at"])
            proxy.modified_at = dateutil.parser.isoparse(i["modified_at"])
            proxy.save()


def import_from_csv(owner_id):
    # sites
    sites = {}  # by url
    with open("site.csv", "r") as f:
        r = csv.DictReader(f, delimiter=",")
        for i in r:
            sites[i["url"]] = i
    logger.info(f"got {len(sites)} sites")

    for url, info in sites.items():
        print(url)
        site = Site.objects.filter(url=url).first()
        if site:
            logger.info("  wiping old checks pre 2021-01-03")
            Check.objects.filter(site=site).filter(
                created_at__lt=datetime.datetime(year=2021, month=1, day=3).replace(
                    tzinfo=datetime.timezone.utc
                )
            ).delete()
        else:
            site = Site.objects.create(
                url=url,
                description=info["description"],  # turnout will adjust this
                owner_id=owner_id,
            )

        # import checks
        print("  importing checks")
        with open("check.csv", "r") as f:
            r = csv.DictReader(f, delimiter=",")
            for i in r:
                if i["site_id"] != info["uuid"]:
                    continue
                if i["ignore"] == "t":
                    continue
                # print(i)

                error = i["error"]
                if i["state_up"]:
                    status = enums.CheckStatus.UP
                elif i["blocked"]:
                    status = enums.CheckStatus.BLOCKED
                else:
                    status, error = classify_check(i["title"], i["content"])
                proxy, _ = Proxy.objects.get_or_create(
                    uuid=i["proxy_id"], source="digitalocean"
                )
                check = Check.objects.create(
                    site=site,
                    status=status,
                    error=error,
                    load_time=i["load_time"],
                    proxy=proxy,
                    ignore=i["ignore"],
                    content=Content.objects.create(
                        title=i["title"], content=i["content"],
                    ),
                )
                check.created_at = dateutil.parser.isoparse(i["created_at"])
                check.save()


def import_leouptime(owner_id):
    # sites
    nexturl = "https://api.voteamerica.com/v1/leouptime/sites/"
    sites = {}  # url -> dict
    while nexturl:
        response = requests.get(nexturl)
        nexturl = response.json().get("next")
        for item in response.json().get("results", []):
            sites[item["url"]] = item

    logger.info(f"got {len(sites)} sites")

    for url, info in sites.items():
        logger.info(url)
        site = Site.objects.filter(url=url).first()
        if site:
            if site.status:
                logger.info("  has status, skipping")
                continue
            logger.info("  wiping old checks")
            Check.objects.filter(site=site).delete()
        else:
            site = Site.objects.create(
                url=url,
                description=info["description"],  # turnout will adjust this
                owner_id=owner_id,
            )

        nexturl = (
            f"https://api.voteamerica.com/v1/leouptime/sites/{info['uuid']}/checks/"
        )
        while nexturl:
            response = requests.get(nexturl)
            nexturl = response.json().get("next")
            for i in response.json().get("results", []):
                if i["ignore"]:
                    continue
                error = i["error"]
                if i["state_up"]:
                    status = enums.CheckStatus.UP
                elif i["blocked"]:
                    status = enums.CheckStatus.BLOCKED
                else:
                    status, error = classify_check(i["title"], i["content"])
                proxy, _ = Proxy.objects.get_or_create(uuid=i["proxy"])
                check = Check.objects.create(
                    site=site,
                    status=status,
                    error=error,
                    load_time=i["load_time"],
                    proxy=proxy,
                    ignore=i["ignore"],
                    content=Content.objects.create(
                        title=i["title"], content=i["content"],
                    ),
                )
                check.created_at = dateutil.parser.isoparse(i["created_at"])
                check.save()

        site.rebuild_downtimes()
