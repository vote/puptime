import datetime
import logging
import random

from selenium.common.exceptions import (
    RemoteDriverServerException,
    SessionNotCreatedException,
    WebDriverException,
)

from common import enums
from uptime.selenium import get_driver, get_drivers

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
    logger.info("Checking all {len(sites)} sites")
    drivers = get_drivers()
    random.shuffle(sites)
    for site in sites:
        check_site(drivers, site)


def check_site(drivers, site):
    # first try primary proxy
    check = check_site_with_pos(drivers, 0, site)

    bad_proxy = False
    if not check.state_up or check.blocked:
        # try another proxy
        check2 = check_site_with_pos(drivers, 1, site)

        if check2.state_up and not check2.blocked:
            # new proxy is fine; ignore the failure

            # check again
            check3 = check_site_with_pos(drivers, 0, site)
            if check3.state_up and not check3.blocked:
                # call it intermittent; stick with original proxy
                check = check3
            else:
                # we've burned the proxy
                logger.warning(f"We've burned {drivers[0][1]} on site {site}")
                drivers[0][1].failure_count += 1
                drivers[0][1].state = enums.ProxyStatus.BURNED
                drivers[0][1].save()

                check = check2

                bad_proxy = True
        else:
            # verify sentinel site loads
            sentinel = Site.get_sentinel_site()
            check4 = check_site_with_pos(drivers, 0, sentinel)
            if not check4.state_up:
                raise NoProxyError("cannot reach sentinel site with original proxy")
            check5 = check_site_with_pos(drivers, 1, sentinel)
            if not check5.state_up:
                raise NoProxyError("cannot reach sentinel site with backup proxy")

            # sentinel looks okay; do not ignore the failurex
            check.ignore = False
            check.save()

    if site.state_up != check.state_up:
        site.state_up = check.state_up
        site.state_changed_at = check.created_at
        if check.state_up:
            downtime = None
            if site.last_went_down_check:
                downtime = Downtime.objects.filter(
                    site=site, first_down_check__isnull=True
                ).first()
            if downtime:
                print(f"downtime is {downtime}")
                downtime.up_check = check
                downtime.save()
                site.last_went_up_check = check
        else:
            Downtime.objects.create(
                site=site,
                first_down_check=check,
                last_down_check=check,
            )
            site.last_went_down_check = check
    elif not check.state_up:
        # update the current downtime
        downtime = None
        if site.last_went_down_check:
            downtime = Downtime.objects.filter(
                site=site, first_down_check__isnull=True
            ).first()
        if downtime:
            downtime.last_down_check = check
            downtime.save()

    if site.blocked != check.blocked:
        site.blocked = check.blocked
        site.blocked_changed_at = check.created_at
        if site.blocked:
            site.last_went_blocked_check = check
        else:
            site.last_went_unblocked_check = check

    site.calc_uptimes()
    site.save()

    if bad_proxy:
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


def check_site_with(driver, proxy, site):
    logger.debug(f"Checking {site} with {proxy}")
    error = None
    timeout = None
    title = ""
    content = ""
    before = datetime.datetime.utcnow()
    try:
        driver.get(site.url)
        if site.description == "test" and not random.choice([0, 1]):
            up = False
            title = "fake down title"
            content = "fake down content"
        else:
            up = True
            title = driver.title
            content = driver.page_source
    except SessionNotCreatedException as e:
        raise e
    except RemoteDriverServerException as e:
        raise e
    except Exception as e:
        if "Timed out receiving message from renderer: -" in str(e):
            # if we get a negatime timeout it's because the worker is broken
            raise SeleniumError(f"Problem talking to selenium worker: {e}")
        if "establishing a connection" in str(e):
            raise e
        if "marionette" in str(e):
            raise e
        if "timeout" in str(e):
            # we may tolerate timeout in some cases; see below
            timeout = str(e)
            up = True
        else:
            up = False
            error = str(e)
    after = datetime.datetime.utcnow()
    dur = after - before

    ignore = False
    blocked = False
    burn = False

    # blocked?
    BURN_LIST = [
        "Request unsuccessful. Incapsula incident ID",
        "<html><head></head><body></body></html>",
    ]
    """
    if get_feature_bool("leouptime", "enable_burn_list"):
        for b in BURN_LIST:
            if b in content:
                blocked = True
                ignore = True
                # make sure we've used this proxy on this site before...
                if SiteCheck.objects.filter(
                    site=site, proxy=proxy, state_up=True, blocked=False
                ).exists():
                    error = f"Proxy is burned (page contains '{b}')"
                    burn = True
                    break
                else:
                    logger.warning(
                        f"Not burning {proxy} on {site} that has never successfully checked it before"
                    )
    """

    if up and not blocked:
        # the trick is determining if this loaded the real page or some sort of error/404 page.
        for item in ["404", "not found", "error"]:
            if item in title.lower():
                up = False
                error = f"'{item}' in page title"
        for item in ["network outage"]:
            if item in content.lower():
                up = False
                error = f"'{item}' in page content"

        REQUIRED_STRINGS = [
            "vote",
            "Vote",
            "Poll",
            "poll",
            "Absentee",
            "ballot",
            "Please enable JavaScript to view the page content.",  # for CT
            "application/pdf",  # for WY
        ]
        have_any = False
        for item in REQUIRED_STRINGS:
            if item in content:
                have_any = True
        if not have_any:
            up = False
            if timeout:
                error = timeout
            else:
                error = f"Cannot find any of {REQUIRED_STRINGS} not in page content"

    # Important: we ignore down checks until we have confirmed the result
    if not up:
        ignore = True

    check = Check.objects.create(
        site=site,
        state_up=up,
        blocked=blocked,
        load_time=dur.total_seconds(),
        error=error,
        proxy=proxy,
        ignore=ignore,
        title=title,
        content=content,
    )

    if burn:
        logger.info(f"BURNED PROXY: {site} ({error}) duration {dur}, {proxy}")
        proxy.failure_count += 1
        proxy.state = enums.ProxyStatus.BURNED
        proxy.save()
        raise StaleProxyError

    if blocked:
        logger.info(f"BLOCKED: {site} ({error}) duration {dur}, {proxy}")
    elif up:
        logger.info(f"UP: {site} ({error}) duration {dur}, {proxy}")
    else:
        logger.info(f"DOWN: {site} ({error}) duration {dur}, {proxy}")

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
