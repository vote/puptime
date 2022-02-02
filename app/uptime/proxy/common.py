import datetime
import logging
import random
import tempfile
import time

import paramiko
from django.db.models import Q
from django.utils import timezone

from common import enums
from common.util import safe_while
from uptime.models import Proxy
from uptime.selenium import get_driver, test_driver

from . import digitalocean, ec2

logger = logging.getLogger("uptime")

from django.conf import settings

PROXY_TYPES = {
    "digitalocean": {"cls": digitalocean.DigitalOceanProxy, "target": 1,},
    "ec2": {"cls": ec2.EC2Proxy, "target": 1,},
}

PROXY_PORT_MIN = 40000
PROXY_PORT_MAX = 60000


def check():
    cleanup()
    test_proxies()
    create_proxies()


def cleanup():
    logger.info("Cleaning up proxies")

    # remove oldest proxy?
    oldest = (
        Proxy.objects.filter(status=enums.ProxyStatus.UP).order_by("created_at").first()
    )
    if oldest:
        if timezone.now() - oldest.created_at > datetime.timedelta(
            hours=settings.MAX_PROXY_AGE_HOURS
        ):
            logger.info(f"Marking RETIRED oldest {oldest}")
            oldest.status = enums.ProxyStatus.RETIRED
            oldest.save()

    # kill old retired|burned proxies?
    for proxy in Proxy.objects.filter(
            Q(status=enums.ProxyStatus.RETIRED)
            | Q(status=enums.ProxyStatus.BURNED)
    ).order_by(
        "created_at"
    ):
        if timezone.now() - proxy.modified_at > datetime.timedelta(minutes=30):
            logger.info(f"Marking DOWN {proxy}")
            proxy.status = enums.ProxyStatus.DOWN
            proxy.save()
        else:
            logger.info(f"Keeping {proxy} for a bit")

    for source, info in PROXY_TYPES.items():
        cls = info["cls"]
        cls.cleanup()


def test_proxies():
    ls = Proxy.objects.filter(status=enums.ProxyStatus.UP)
    logger.info(f"Testing {len(ls)} UP proxies")
    bad = []
    for proxy in ls:
        driver = get_driver(proxy)
        if not test_driver(driver):
            bad.append(proxy)
        driver.quit()

    if bad:
        if len(bad) == len(ls):
            logger.warn("All proxies appear down; there is probably something wrong")
        else:
            for proxy in bad:
                logger.info(
                    f"Marking {proxy} BURNED for failing to reach sentinel site"
                )
                proxy.status = enums.ProxyStatus.BURNED
                proxy.save()


def create_proxies():
    for source, info in PROXY_TYPES.items():
        cls = info["cls"]
        target = info["target"]

        for region in cls.get_regions():
            proxies = Proxy.objects.filter(
                status=enums.ProxyStatus.UP,
                source=source,
                region=region)
            num_up = len(proxies)
            if num_up < target:
                want = target - num_up
                logger.info(f"Have {num_up}/{target} {source} {region} proxies, creating {want}")
                for i in range(want):
                    cls.create(region)
            else:
                logger.info(f"Have {num_up}/{target} {source} {region} proxies")


def proxy_is_up(address: str, timeout: int = 3) -> bool:
    import socket
    import struct

    sen = struct.pack("BBB", 0x05, 0x01, 0x00)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host, port = address.split(":")
    s.settimeout(timeout)
    try:
        s.connect((host, int(port)))
        s.sendall(sen)

        data = s.recv(2)

        version, auth = struct.unpack("BB", data)
        s.close()
        logger.info(f"proxy {address}, version {version}, auth {auth}")
        return version == 5 and auth == 0

    except socket.timeout:
        logger.info(f"proxy {address} timed out")
        return False
    except Exception as e:
        logger.info(f"proxy {address} failed: {e}")
        return False


def create_ubuntu_proxy(source, region, name, ip, metadata, user):
    port = random.randint(PROXY_PORT_MIN, PROXY_PORT_MAX)

    metadata.update(
        {"tag": settings.PROXY_TAG,}
    )
    proxy = Proxy.objects.create(
        source=source,
        region=region,
        address=f"{ip}:{port}",
        description=name,
        status=enums.ProxyStatus.CREATING,
        failure_count=0,
        metadata=metadata,
    )

    if user == "root":
        home = "/root"
    else:
        home = f"/home/{user}"

    UNITFILE = f"""[Unit]
Description=microsocks
After=network.target
[Service]
ExecStart={home}/microsocks/microsocks -p {port}
[Install]
WantedBy=multi-user.target
"""
    SETUP = [
        f"sudo hostname {proxy.description}",
        f"echo {proxy.description} > sudo tee /etc/hostname",
        "sudo apt update",
        "sudo apt install -y gcc make",
        "git clone https://github.com/rofl0r/microsocks",
        "cd microsocks && make",
        "sudo systemctl enable microsocks.service",
        "sudo systemctl start microsocks.service",
    ]

    with tempfile.NamedTemporaryFile() as tmp_key:
        tmp_key.write(settings.PROXY_SSH_KEY)
        tmp_key.flush()

        # logger.info(f"IP is {ip}, waiting for machine to come up...")
        # time.sleep(60)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        with safe_while(sleep=5, tries=30) as proceed:
            while proceed():
                try:
                    logger.info(f"Connecting to {ip} via SSH...")
                    ssh.connect(
                        ip, username=user, key_filename=tmp_key.name, timeout=10
                    )
                    break
                except:
                    logger.info("Waiting a bit...")

        logger.info("Writing systemd unit...")
        stdin_, stdout_, stderr_ = ssh.exec_command(
            "cat | sudo tee /etc/systemd/system/microsocks.service"
        )
        stdin_.write(UNITFILE)
        stdin_.close()
        stdout_.channel.recv_exit_status()

        logger.info("Waiting a few seconds for release-upgrader thing to run...")
        time.sleep(15)

        for cmd in SETUP:
            logger.info(f"  # {cmd}")
            stdin_, stdout_, stderr_ = ssh.exec_command(cmd)
            stdout_.channel.recv_exit_status()
            lines = stdout_.readlines()
            for line in lines:
                logger.info(f"  {line.strip()}")

    if not proxy_is_up(f"{ip}:{port}"):
        logger.warning(f"new proxy {ip}:{port} does not appear to be reachable")
        return

    proxy.status = enums.ProxyStatus.UP
    proxy.save()

    logger.info(f"Configured proxy {proxy}")
