import logging

import dateutil
import requests

from common import enums

from .check import classify_check
from .models import Check, Proxy, Site

logger = logging.getLogger("uptime")


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
                    title=i["title"],
                    ignore=i["ignore"],
                )
                check.created_at = dateutil.parser.isoparse(i["created_at"])
                check.save()

        site.rebuild_downtimes()
