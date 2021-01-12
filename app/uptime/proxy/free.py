import logging

import requests

from uptime.models import Proxy
from uptime.proxy import proxy_is_up

logger = logging.getLogger("uptime")


def injest(ls, source):
    logger.info(f"Processing {len(ls)} proxies from {source}")
    had = 0
    for address in ls:
        proxy = Proxy.objects.filter(address=address).first()
        if proxy:
            # exists
            # FIXME: resurrect if down/burned maybe?
            had += 1
            continue
        if not proxy_is_up(address):
            continue

        proxy = Proxy.objects.create(
            address=address,
            source=source,
            status="up",
        )
        logger.info(f"Created {proxy}")
    logger.info(f"Already had the {had} others from {source}")


def scrape_proxy_list_download():
    url = "https://www.proxy-list.download/api/v0/get?l=en&t=socks5"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception:
        logger.warning("Failed to scrape from {url}: {e}")
        return

    proxies = []

    for item in response.json()[0].get("LISTA", []):
        if item["COUNTRY"] == "United States":
            proxies.append(f"{item['IP']}:{item['PORT']}")

    injest(proxies, "proxy-list.download")


def scrape_pubproxy_com():
    url = "http://pubproxy.com/api/proxy?type=socks5&limit=5&https=true"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to scrape from {url}: {e}")
        return
    proxies = []

    for item in response.json().get("data", []):
        proxies.append(f"{item['ip']}:{item['port']}")
    injest(proxies, "pubproxy.com")


def scrape_all():
    scrape_proxy_list_download()
    scrape_pubproxy_com()
