import logging

from common import enums
from uptime.check import get_sentinel_site
from uptime.models import Proxy

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
    logger.info("Testing proxies")
    ls = Proxy.objects.filter(status=enums.ProxyStatus.UP)
    site = get_sentinel_site()
    logger.info(f"Testing {len(ls)} UP proxies against sentinel {site}")
    bad = []
    for proxy in ls:
        driver = get_driver(proxy)
        check = check_site_with(driver, proxy, site)
        if not check["state_up"]:
            bad.append(proxy)
    if bad:
        if len(bad) == len(ls):
            logger.warn("All proxies appear down; there is probably something wrong")
        else:
            for proxy in bad:
                logger.info(
                    "Marking {proxy} BURNED for failing to reach sentinel {site}"
                )
                proxy.status = enums.ProxyStatus.BURNED


def create_proxies(cls=PROXY_TYPES[0]):
    logger.info("Creating proxies")
    proxies = Proxy.objects.filter(status=enums.ProxyStatus.UP)
    num_up = len(proxies)

    if num_up < settings.PROXY_TARGET:
        want = settings.PROXY_TARGET - num_up
        logger.info(f"Have {num_up}/{settings.PROXY_TARGET} proxies, creating {want}")
        for i in range(want):
            cls.create()
    else:
        logger.info(f"Have {num_up}/{settings.PROXY_TARGET} proxies")


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
    logger.info(f"Created driver for {proxy}")
    return driver


def get_drivers():
    drivers = []

    unused_proxies = list(
        Proxy.objects.filter(
            status=enums.ProxyStatus.UP, last_used__isnull=True
        ).order_by("failure_count", "created_at")
    )
    used_proxies = list(
        Proxy.objects.filter(status=enums.ProxyStatus.UP).order_by(
            "failure_count",
            "last_used",
        )
    )

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
    logger.info(f"backup {backup} last_used {backup['last_used']}")
    logger.info(f"primary {primary} last_used {primary['last_used']}")
    drivers.append([get_driver(primary), primary])
    drivers.append([get_driver(backup), backup])

    primary.last_used = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    primary.save()

    return drivers
