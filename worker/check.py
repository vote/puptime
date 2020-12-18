import os
import datetime
import logging
import random
import uuid

import requests

from selenium import webdriver
from selenium.common.exceptions import (
    RemoteDriverServerException,
    SessionNotCreatedException,
    WebDriverException,
)

from common import psite, pproxy, pcheck
import proxy


logger = logging.getLogger("uptime")


class SeleniumError(Exception):
    pass


class NoProxyError(Exception):
    pass


class StaleProxyError(Exception):
    pass


class BurnedProxyError(Exception):
    pass


def get_sentinel_site(client):
    sites = client.list('sites', {'description': 'sentinel'})
    assert sites
    return sites[0]


def check_all(client):
    drivers = proxy.get_drivers(client)
    sites = client.list('sites')
    random.shuffle(sites)
    for site in sites:
        check_site(client, drivers, site)


def check_site(client, drivers, site):
    # first try primary proxy
    check = check_site_with_pos(client, drivers, 0, site)
    bad_proxy = False
    if not check["state_up"] or check["blocked"]:
        # try another proxy
        check2 = check_site_with_pos(client, drivers, 1, site)

        if check2["state_up"] and not check2["blocked"]:
            # new proxy is fine; ignore the failure
            check.ignore = True
            check.save()

            check3 = check_site_with_pos(client, drivers, 0, site)
            if check3["state_up"] and not check3["blocked"]:
                # call it intermittent; stick with original proxy
                check = check3
            else:
                # we've burned the proxy
                logger.warning(f"We've burned {drivers[0][1]} on site {psite(site)}")
                drivers[0][1].failure_count += 1
                drivers[0][1].state = enums.ProxyStatus.BURNED
                drivers[0][1].save()

                check = check2

                check3.ignore = True
                check3.save()

                bad_proxy = True
        else:
            # verify sentinel site loads
            sentinel = get_sentinel_site(client)
            check4 = check_site_with_pos(client, drivers, 0, sentinel)
            if not check4["state_up"]:
                raise NoProxyError("cannot reach sentinel site with original proxy")
            check5 = check_site_with_pos(client, drivers, 1, sentinel)
            if not check5["state_up"]:
                raise NoProxyError("cannot reach sentinel site with backup proxy")

    if site["state_up"] != check["state_up"]:
        site["state_up"] = check["state_up"]
        site["state_changed_at"] = check["created_at"]
        if check["state_up"]:
            downtime = None
            if site["last_went_down_check"]:
                for d in client.list('downtimes', {
                        "site": site["uuid"],
                        "down_check": site["last_went_down_check"],
                }):
                    downtime = d
                    break
            if downtime:
                print(f"downtime is {downtime}")
                client.update(
                    "downtimes",
                    downtime["uuid"],
                    {
                        "up_check": check["uuid"]
                    }
                )
                site["last_went_up_check"] = check["uuid"]
        else:
            client.create(
                "downtimes",
                {
                    "site": site["uuid"],
                    "down_check": check["uuid"]
                }
            )
            site["last_went_down_check"] = check["uuid"]

    if site["blocked"] != check["blocked"]:
        site["blocked"] = check["blocked"]
        site["blocked_changed_at"] = check["created_at"]
        if site["blocked"]:
            site["last_went_blocked_check"] = check["uuid"]
        else:
            site["last_went_unblocked_check"] = check["uuid"]

#    site.calc_uptimes()
    client.update(
        "sites",
        site["uuid"],
        site
    )

    if bad_proxy:
        raise StaleProxyError()


def check_site_with_pos(client, drivers, pos, site):
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
                drivers[pos][0] = proxy.get_driver(drivers[pos][1])
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
            check = check_site_with(client, drivers[pos][0], drivers[pos][1], site)
            if check["error"] and "timeout" in check["error"]:
                reset_selenium()
            break
        except SeleniumError as e:
            logger.info(f"Selenium error on try {tries}: {e}")
            if tries > 2:
                raise e
            reset_selenium()

    return check


def check_site_with(client, driver, proxy, site):
    logger.debug(f"Checking {psite(site)} with {pproxy(proxy)}")
    error = None
    timeout = None
    title = ""
    content = ""
    before = datetime.datetime.utcnow()
    try:
        driver.get(site["url"])
        if site["description"] == "test" and not random.choice([0,1]):
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
                        f"Not burning {pproxy(proxy)} on {psite(site)} that has never successfully checked it before"
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

    # ignore down checks until we have confirmed
    if not up:
        ignore = True

    check = client.create(
        'checks',
        {
            "site": site["uuid"],
            "state_up": up,
            "blocked": blocked,
            "load_time": dur.total_seconds(),
            "error": error,
            "proxy": proxy['uuid'],
            "ignore": ignore,
            "title": title,
#            "content": content,
        }
    )

    if burn:
        logger.info(f"BURNED PROXY: {psite(site)} ({error}) duration {dur}, {pproxy(proxy)}")
        """
        proxy.failure_count += 1
        proxy.state = enums.ProxyStatus.BURNED
        proxy.save()
        """
        raise StaleProxyError

    if blocked:
        logger.info(f"BLOCKED: {psite(site)} ({error}) duration {dur}, {pproxy(proxy)}")
    elif up:
        logger.info(f"UP: {psite(site)} ({error}) duration {dur}, {pproxy(proxy)}")
    else:
        logger.info(f"DOWN: {psite(site)} ({error}) duration {dur}, {pproxy(proxy)}")

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


