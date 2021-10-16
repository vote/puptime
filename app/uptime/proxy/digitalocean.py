import datetime
import logging
import random
import uuid

import requests
from django.conf import settings

from common import enums
from uptime.models import Proxy

PROXY_PREFIX = "proxy-"

REGIONS = [
    "nyc1",
    "nyc3",
    "sfo2",
    "sfo3",
]

CREATE_TEMPLATE = {
    "size": "s-1vcpu-1gb",
    "image": "ubuntu-18-04-x64",
    "ssh_keys": [settings.PROXY_SSH_KEY_ID],
    "backups": False,
    "ipv6": False,
}

DROPLET_ENDPOINT = "https://api.digitalocean.com/v2/droplets"

logger = logging.getLogger("uptime")


class DigitalOceanProxy(object):
    @classmethod
    def create(cls, region=None):
        from uptime.proxy.common import create_ubuntu_proxy

        if not region:
            region = random.choice(REGIONS)

        proxy_uuid = uuid.uuid4()
        name = f"{PROXY_PREFIX}{region}-{str(proxy_uuid)}"

        logger.info(f"Creating {name}...")
        req = CREATE_TEMPLATE.copy()
        req["name"] = name
        req["region"] = region
        req["tags"] = [f"env:{settings.PROXY_TAG}"]
        response = requests.post(
            DROPLET_ENDPOINT,
            headers={
                "Authorization": f"Bearer {settings.DIGITALOCEAN_KEY}",
                "Content-Type": "application/json",
            },
            json=req,
        )
        logger.debug(response.json())
        droplet_id = response.json()["droplet"]["id"]

        # wait for IP address
        logger.info(f"Created {name} droplet_id {droplet_id}, waiting for IP...")
        ip = None
        with safe_while(sleep=1, tries=60):
            while proceed():
                response = requests.get(
                    f"{DROPLET_ENDPOINT}/{droplet_id}",
                    headers={
                        "Authorization": f"Bearer {settings.DIGITALOCEAN_KEY}",
                        "Content-Type": "application/json",
                    },
                )
                for v4 in response.json()["droplet"]["networks"].get("v4", []):
                    if v4["type"] == "public":
                        ip = v4["ip_address"]
                        break
                if ip:
                    break
                logger.info("waiting for IP")

        create_ubuntu_proxy(
            "digitalocean",
            name,
            ip,
            {"region": region, "droplet_id": droplet_id,},
            "root",
        )

    @classmethod
    def remove_droplet(cls, droplet_id):
        logger.info(f"Removing droplet {droplet_id}")
        response = requests.delete(
            f"{DROPLET_ENDPOINT}/{droplet_id}/destroy_with_associated_resources/dangerous",
            headers={
                "Authorization": f"Bearer {settings.DIGITALOCEAN_KEY}",
                "Content-Type": "application/json",
                "X-Dangerous": "true",
            },
        )

    @classmethod
    def remove_proxy(cls, proxy):
        logger.info(f"Removing proxy {proxy}")
        cls.remove_droplet(proxy.metadata.get("droplet_id"))

    @classmethod
    def get_proxies_by_name(cls):
        r = {}
        nexturl = DROPLET_ENDPOINT
        while nexturl:
            response = requests.get(
                nexturl,
                headers={
                    "Authorization": f"Bearer {settings.DIGITALOCEAN_KEY}",
                    "Content-Type": "application/json",
                },
            )
            for droplet in response.json().get("droplets", []):
                if f"env:{settings.PROXY_TAG}" in droplet["tags"]:
                    r[droplet["name"]] = droplet
            nexturl = response.json().get("links", {}).get("pages", {}).get("next")
        return r

    @classmethod
    def cleanup(cls):
        logger.info("Cleanup enumerating digitalocean proxies...")
        stray = cls.get_proxies_by_name()
        logger.info(
            f"Found {len(stray)} running proxies under tag env:{settings.PROXY_TAG}"
        )
        creating_cutoff = datetime.datetime.utcnow().replace(
            tzinfo=datetime.timezone.utc
        ) - datetime.timedelta(minutes=10)

        for proxy in Proxy.objects.filter(source="digitalocean"):
            if proxy.description in stray:
                if proxy.status == enums.ProxyStatus.DOWN:
                    # we should delete this
                    logger.info(f"Proxy {proxy} marked Down")
                elif (
                    proxy.status == enums.ProxyStatus.CREATING
                    and proxy.modified_at < creating_cutoff
                ):
                    # delete
                    logger.info(f"Proxy {proxy} has been Creating for too long")
                    proxy.delete()
                else:
                    # keep
                    del stray[proxy.description]
            else:
                if proxy.status != enums.ProxyStatus.DOWN:
                    logger.info(f"No droplet for proxy {proxy}, marking Down")
                    proxy.status = enums.ProxyStatus.DOWN
                    proxy.save()

        for name, info in stray.items():
            if not name.startswith(PROXY_PREFIX):
                continue
            logger.info(f"Removing stray droplet {name} {info['id']}")
            cls.remove_droplet(info["id"])
        logger.info("Cleanup done")
