import logging

from common import enums
from uptime.check import check_site_with
from uptime.models import Proxy, Site
from uptime.selenium import get_driver

from . import digitalocean

logger = logging.getLogger("uptime")

from app import settings

PROXY_TYPES = [digitalocean.DigitalOceanProxy]


def check():
    cleanup()
    test_proxies()
    create_proxies()


def cleanup():
    logger.info("Cleaning up proxies")
    for cls in PROXY_TYPES:
        cls.cleanup()


def test_proxies():
    ls = Proxy.objects.filter(status=enums.ProxyStatus.UP)
    site = Site.get_sentinel_site()
    logger.info(f"Testing {len(ls)} UP proxies against sentinel {site}")
    bad = []
    for proxy in ls:
        driver = get_driver(proxy)
        check = check_site_with(driver, proxy, site)
        if not check.state_up:
            bad.append((check, proxy))
    if bad:
        if len(bad) == len(ls):
            logger.warn("All proxies appear down; there is probably something wrong")
        else:
            for check, proxy in bad:
                logger.info(
                    f"Marking {proxy} BURNED for failing to reach sentinel {site}"
                )
                proxy.status = enums.ProxyStatus.BURNED
                proxy.save()


def create_proxies(cls=PROXY_TYPES[0]):
    proxies = Proxy.objects.filter(status=enums.ProxyStatus.UP)
    num_up = len(proxies)

    if num_up < settings.PROXY_TARGET:
        want = settings.PROXY_TARGET - num_up
        logger.info(f"Have {num_up}/{settings.PROXY_TARGET} proxies, creating {want}")
        for i in range(want):
            cls.create()
    else:
        logger.info(f"Have {num_up}/{settings.PROXY_TARGET} proxies")
