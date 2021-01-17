import datetime
import logging
import random
import uuid

from selenium import webdriver
from selenium.common.exceptions import (
    RemoteDriverServerException,
    SessionNotCreatedException,
)

from common import enums
from uptime.models import Proxy

logger = logging.getLogger("uptime")

from app import settings

# These are from https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36	",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
]


def get_driver(proxy):
    options = webdriver.ChromeOptions()
    options.add_argument(f"--proxy-server=socks5://{proxy.address}")

    # https://stackoverflow.com/questions/48450594/selenium-timed-out-receiving-message-from-renderer
    options.add_argument("--disable-gpu")
    options.add_argument("enable-automation")
    options.add_argument("--headless")
    options.add_argument("--window-size=1024,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument("--dns-prefetch-disable")
    options.add_argument(f"--user-agent={random.choice(AGENTS)}")
    options.add_argument(
        "--disable-browser-side-navigation"
    )  # https://stackoverflow.com/a/49123152/1689770

    # random independent user dir
    #options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{uuid.uuid4()}")

    caps = webdriver.DesiredCapabilities.CHROME.copy()
    caps["pageLoadStrategy"] = "normal"

    driver = webdriver.Remote(
        command_executor=settings.SELENIUM_URL,
        desired_capabilities=caps,
        options=options,
    )
    driver.set_page_load_timeout(settings.SELENIUM_DRIVER_TIMEOUT)
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

    # randomly shuffle remaining proxies
    random.shuffle(proxies)

    # verify the proxy is responding before we try to use it
    verified = []
    while len(verified) < 2:
        from uptime.proxy import proxy_is_up

        if not proxies:
            logger.warning(f"failed to find 2 working proxies")
            raise NoProxyError(f"failed to find 2 working proxies")

        proxy = proxies.pop()
        if proxy_is_up(proxy.address):
            verified.append(proxy)

    backup = verified[0]
    primary = verified[1]
    logger.info(f"backup {backup} last_used {backup.last_used}")
    logger.info(f"primary {primary} last_used {primary.last_used}")
    drivers.append([get_driver(primary), primary])
    drivers.append([get_driver(backup), backup])

    primary.last_used = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    primary.save()

    return drivers


def test_driver(driver):
    try:
        nonce = str(random.randint(1000000, 9999999))
        url = f"{settings.PRIMARY_ORIGIN}/test/{nonce}/"
        driver.get(url)
        if nonce in driver.page_source:
            return True
        return False
    except SessionNotCreatedException as e:
        raise e
    except RemoteDriverServerException as e:
        raise e
    except Exception as e:
        logger.info(e)
        return False


def load_site(driver, url):
    error = None
    timeout = None
    title = ""
    content = ""
    png = None

    try:
        driver.get(url)
        title = driver.title
        content = driver.page_source
        png = driver.get_screenshot_as_png()
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
        else:
            error = str(e)

    return error, timeout, title, content, png
