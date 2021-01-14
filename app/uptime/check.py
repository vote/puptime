import datetime
import logging
import random
from typing import Tuple

from django.conf import settings
from selenium.common.exceptions import (
    RemoteDriverServerException,
    SessionNotCreatedException,
    WebDriverException,
)

from common import enums
from common.aws import s3_client
from uptime.selenium import get_driver, get_drivers, test_driver, load_site

from .models import Check, Downtime, Site

logger = logging.getLogger("uptime")


class SeleniumError(Exception):
    pass


class NoProxyError(Exception):
    pass


class StaleProxyError(Exception):
    pass


class BurnedProxyError(Exception):
    pass


def check_all():
    sites = list(Site.objects.filter(active=True))
    logger.info(f"Checking all {len(sites)} sites")
    drivers = get_drivers()
    random.shuffle(sites)
    while sites:
        site = sites.pop()
        try:
            check_site(drivers, site)
        except StaleProxyError:
            logger.info("Refreshing proxies")
            for item in drivers:
                item[0].quit()
            drivers = get_drivers()

    for item in drivers:
        item[0].quit()


def check_site(drivers, site):
    # try proxies in order
    failures = []
    burned_proxies = []
    for pos in range(len(drivers)):
        check = check_site_with_pos(drivers, pos, site)
        if check.status == enums.CheckStatus.UP:
            break
        if check.status == enums.CheckStatus.BLOCKED:
            burned_proxies.append(check)
        else:
            failures.append(check)

    if check.status == enums.CheckStatus.UP:
        # re-check failures to see if they were transient issues or the proxies' fault
        for pos in range(len(failures)):
            recheck = check_site_with_pos(drivers, pos, site)
            if recheck.status == failures[pos].status:
                proxy = drivers[pos][1]
                logger.info(f"Proxy {proxy} appears to be burned")
                burned_proxies.append(proxy)
            else:
                logger.info(
                    f"Proxy {proxy} got different result ({failures[pos].status} vs {recheck.status})"
                )
    else:
        # all attempts were either DOWN or BURNED
        for check in failures:
            check.ignore = False
            check.save()

        if failures:
            # go with the first failure
            check = failures[0]

    if check.status != site.status:
        if check.status == enums.CheckStatus.DOWN:
            site.last_downtime = Downtime.objects.create(
                site=site,
                first_down_check=failures[0],
                last_down_check=failures[-1],
            )
        elif check.status == enums.CheckStatus.UP and site.last_downtime:
            site.last_downtime.up_check = check
            site.last_downtime.save()
            site.last_downtime = None

        if site.status == enums.CheckStatus.BLOCKED:
            site.last_went_unblocked_check = check
        if check.status == enums.CheckStatus.BLOCKED:
            site.last_went_blocked_check = check

        site.status = check.status
        site.status_changed_at = check.created_at

    elif check.status == enums.CheckStatus.DOWN:
        # update the current downtime
        if site.last_downtime:
            site.last_downtime.last_down_check = check
            site.last_downtime.save()

    site.calc_uptimes()
    site.save()

    for proxy in burned_proxies:
        proxy.state = enums.ProxyStatus.BURNED
        proxy.save()
        raise StaleProxyError()


def check_site_with_pos(drivers, pos, site):
    def reset_selenium():
        reset_tries = 0
        while True:
            reset_tries += 1
            logger.info(f"Reset driver pos {pos} attempt {reset_tries}")
            try:
                drivers[pos][0].quit()
            except WebDriverException as e:
                logger.warning(
                    f"Failed to quit selenium worker for {drivers[pos][1]}: {e}"
                )
            try:
                drivers[pos][0] = get_driver(drivers[pos][1])
                break
            except WebDriverException as e:
                logger.warning(
                    f"Failed to reset driver for {drivers[pos][1]}, reset tries {reset_tries}: {e}"
                )
                if reset_tries > 2:
                    logger.warning(
                        f"Failed to reset driver for {drivers[pos][1]}, reset tries {reset_tries}, giving up"
                    )
                    raise e

    tries = 0
    while True:
        try:
            tries += 1
            check = check_site_with(drivers[pos][0], drivers[pos][1], site)
            if check.error and "timeout" in check.error:
                reset_selenium()
            break
        except SeleniumError as e:
            logger.info(f"Selenium error on try {tries}: {e}")
            if tries > 2:
                raise e
            reset_selenium()

    return check


def classify_check(title: str, content: str) -> Tuple[enums.CheckStatus, str]:
    BLOCK_STRINGS = [
        "Request unsuccessful. Incapsula incident ID",
        #        "<html><head></head><body></body></html>",
    ]
    for s in BLOCK_STRINGS:
        if s in content:
            return enums.CheckStatus.BLOCKED, f"page contains block string '{s}'"

    DOWN_TITLE_STRINGS = ["404", "not found", "error"]
    for s in DOWN_TITLE_STRINGS:
        if s in title.lower():
            return enums.CheckStatus.DOWN, f"title contains string '{s}'"

    BODY_STRINGS = [
        "vote",
        "poll",
        "absentee",
        "ballot",
        "Please enable JavaScript to view the page content.",  # for CT
        "application/pdf",  # for WY
    ]
    lower_content = content.lower()
    for s in BODY_STRINGS:
        if s in lower_content:
            return enums.CheckStatus.UP, None

    return enums.CheckStatus.DOWN, f"page does not contain required string"


def check_site_with(driver, proxy, site):
    logger.debug(f"Checking {site} with {proxy}")

    # first verify the proxy works
    if not test_driver(driver):
        raise StaleProxyError(f"proxy {proxy} cannot reach sentinel")

    before = datetime.datetime.utcnow()
    error, timeout, title, content, png = load_site(driver, site.url)
    after = datetime.datetime.utcnow()
    dur = after - before

    status, reason = classify_check(title, content)

    if timeout and status == enums.CheckStatus.DOWN:
        reason = timeout

    # Important: we ignore non-UP checks until we have confirmed the result
    ignore = False
    if status != enums.CheckStatus.UP:
        ignore = True

    check = Check.objects.create(
        site=site,
        load_time=dur.total_seconds(),
        status=status,
        error=reason,
        proxy=proxy,
        ignore=ignore,
        title=title,
    )

    # upload png and html to s3
    png_filename = str(check.uuid) + ".png"
    html_filename = str(check.uuid) + ".html"
    upload = s3_client.put_object(
        Bucket=settings.SNAPSHOT_BUCKET,
        Key=png_filename,
        ContentType="image/png",
        ACL="public-read",
        Body=png,
    )
    if upload.get("ResponseMetadata", {}).get("HTTPStatusCode") != 200:
        logger.warning(
            f"{number}: Unable to push {png_filename} to {settings.SNAPSHOT_BUCKET}"
        )
    else:
        check.snapshot_url = (
            f"https://{settings.SNAPSHOT_BUCKET}.s3.amazonaws.com/{png_filename}"
        )
    upload = s3_client.put_object(
        Bucket=settings.SNAPSHOT_BUCKET,
        Key=html_filename,
        ContentType="text/html",
        ACL="public-read",
        Body=content,
    )
    if upload.get("ResponseMetadata", {}).get("HTTPStatusCode") != 200:
        logger.warning(
            f"{number}: Unable to push {html_filename} to {settings.SNAPSHOT_BUCKET}"
        )
    else:
        check.content_url = (
            f"https://{settings.SNAPSHOT_BUCKET}.s3.amazonaws.com/{html_filename}"
        )
    check.save()

    logger.info(f"{status}: {site} ({error}) duration {dur}, {proxy}")

    if status == enums.CheckStatus.BLOCKED:
        logger.info(f"BURNED PROXY: {site} ({error}) duration {dur}, {proxy}")
        proxy.failure_count += 1
        proxy.state = enums.ProxyStatus.BURNED
        proxy.save()
        raise StaleProxyError

    return check


def to_pretty_timedelta(n):
    if n < datetime.timedelta(seconds=120):
        return str(int(n.total_seconds())) + "s"
    if n < datetime.timedelta(minutes=120):
        return str(int(n.total_seconds() // 60)) + "m"
    if n < datetime.timedelta(hours=48):
        return str(int(n.total_seconds() // 3600)) + "h"
    if n < datetime.timedelta(days=14):
        return str(int(n.total_seconds() // (24 * 3600))) + "d"
    if n < datetime.timedelta(days=7 * 12):
        return str(int(n.total_seconds() // (24 * 3600 * 7))) + "w"
    if n < datetime.timedelta(days=365 * 2):
        return str(int(n.total_seconds() // (24 * 3600 * 30))) + "M"
    return str(int(n.total_seconds() // (24 * 3600 * 365))) + "y"
