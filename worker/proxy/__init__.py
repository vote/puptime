import time
import tempfile
import paramiko
import random
import os
import requests
import uuid
import logging
import datetime

from . import digitalocean
from common import pproxy, psite
from check import check_site_with, get_sentinel_site
from selenium import webdriver
from selenium.common.exceptions import (
    RemoteDriverServerException,
    SessionNotCreatedException,
    WebDriverException,
)

DRIVER_TIMEOUT = 30

PROXY_TARGET = int(os.getenv("PROXY_TARGET", 5))

logger = logging.getLogger("proxy")


PROXY_TYPES = [
    digitalocean.DigitalOceanProxy
]

def check(client):
    cleanup(client)
    test_proxies(client)
    create_proxies(client)


def cleanup(client):
    for cls in PROXY_TYPES:
        cls.cleanup(client)
        

def test_proxies(client):
    ls = client.list('proxies', {"status": "UP"})
    site = get_sentinel_site(client)
    logger.info(f"Testing {len(ls)} UP proxies against sentinel {psite(site)}")
    bad = []
    for proxy in ls:
        driver = get_driver(proxy)
        check = check_site_with(client, driver, proxy, site)
        if not check["state_up"]:
            bad.append(proxy)
    if bad:
        if len(bad) == len(ls):
            logger.warn("All proxies appear down; there is probably something wrong")
        else:
            for proxy in bad:
                logger.info("Marking {pproxy(proxy)} BURNED for failing to reach sentinel {psite(site)}")
                client.update("proxies", proxy["uuid"], {"state": "BURNED"})


def create_proxies(client, cls=digitalocean.DigitalOceanProxy):
    proxies = client.list('proxies')
    num_up = 0
    for proxy in proxies:
        if proxy["state"] == "UP":
            num_up += 1

    if num_up < PROXY_TARGET:
        want = PROXY_TARGET - num_up
        logger.info(f"Have {num_up}/{PROXY_TARGET} proxies, creating {want}")
        for i in range(want):
            cls.create(client)
    else:
        logger.info(f"Have {num_up}/{PROXY_TARGET} proxies")


def get_driver(proxy):
    options = webdriver.ChromeOptions()
    options.add_argument(f"--proxy-server=socks5://{proxy['address']}")

    # https://stackoverflow.com/questions/48450594/selenium-timed-out-receiving-message-from-renderer
    options.add_argument("--disable-gpu")
    options.add_argument("enable-automation")
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument("--dns-prefetch-disable")
    options.add_argument(
        "--disable-browser-side-navigation"
    )  # https://stackoverflow.com/a/49123152/1689770

    # random independent user dir
    options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{uuid.uuid4()}")

    caps = webdriver.DesiredCapabilities.CHROME.copy()
    caps["pageLoadStrategy"] = "normal"

    driver = webdriver.Remote(
        command_executor=os.getenv("SELENIUM_URL", "http://localhost:4444/wd/hub"),
        desired_capabilities=caps,
        options=options,
    )
    driver.set_page_load_timeout(DRIVER_TIMEOUT)
    logger.info(f"Created driver for {pproxy(proxy)}")
    return driver


def get_drivers(client):
    drivers = []

    unused_proxies = client.list('proxies', {"state": "UP", "last_used": None})
    #).order_by("failure_count", "created_at")
    used_proxies = client.list('proxies', {"state": "UP"})
#    
#        Proxy.objects.filter(state=enums.ProxyStatus.UP).order_by(
#            "failure_count", "last_used",
#        )
#    )

    # always try to keep a fresh proxy in reserve, if we can
    if unused_proxies and len(unused_proxies) + len(used_proxies) > 2:
        reserve = unused_proxies.pop()
        logger.debug(f"reserve {reserve}")

    proxies = unused_proxies + used_proxies

    if len(proxies) < 2:
        logger.warning(f"not enough available proxies (only {len(proxies)})")
        raise NoProxyError(f"{len(proxies)} available (need at least 2)")

    # use one as a backup, and a random one as primary
    backup = proxies.pop()
    primary = proxies[0]
    logger.info(f"backup {pproxy(backup)} last_used {backup['last_used']}")
    logger.info(f"primary {pproxy(primary)} last_used {primary['last_used']}")
    drivers.append([get_driver(primary), primary])
    drivers.append([get_driver(backup), backup])

    client.update(
        'proxies',
        primary["uuid"],
        {
            "last_used": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
        }
    )

    return drivers
