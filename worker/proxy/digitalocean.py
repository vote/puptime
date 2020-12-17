import logging
import time
import tempfile
import paramiko
import random
import os
import requests
import uuid
import logging
import datetime


PROXY_PORT_MIN = 2000
PROXY_PORT_MAX = 60000
PROXY_PREFIX = "proxy-"

PROXY_SSH_KEY = os.getenv("PROXY_SSH_KEY").replace("\\n", "\n").encode("utf-8")
PROXY_SSH_KEY_ID = os.getenv("PROXY_SSH_KEY_ID")

DIGITALOCEAN_KEY = os.getenv("DIGITALOCEAN_KEY")

PROXY_TAG = os.getenv("PROXY_TAG")


REGIONS = [
    "nyc1",
    "nyc3",
    "sfo2",
    "sfo3",
]

CREATE_TEMPLATE = {
    "size": "s-1vcpu-1gb",
    "image": "ubuntu-18-04-x64",
    "ssh_keys": [PROXY_SSH_KEY_ID],
    "backups": False,
    "ipv6": False,
}

DROPLET_ENDPOINT = "https://api.digitalocean.com/v2/droplets"

UNITFILE = """
[Unit]
Description=microsocks
After=network.target
[Service]
ExecStart=/root/microsocks/microsocks -p {port}
[Install]
WantedBy=multi-user.target
"""

SETUP = [
    "apt update",
    "apt install -y gcc make",
    "git clone https://github.com/rofl0r/microsocks",
    "cd microsocks && make",
    "systemctl enable microsocks.service",
    "systemctl start microsocks.service",
]



logger = logging.getLogger()



class DigitalOceanProxy(object):

    @classmethod
    def create(cls, client, region=None):
        if not region:
            region = random.choice(REGIONS)

        proxy_uuid = uuid.uuid4()
        name = f"{PROXY_PREFIX}{region}-{str(proxy_uuid)}"

        logger.info(f"Creating {name}...")
        req = CREATE_TEMPLATE.copy()
        req["name"] = name
        req["region"] = region
        req["tags"] = [PROXY_TAG]
        response = requests.post(
            DROPLET_ENDPOINT,
            headers={
                "Authorization": f"Bearer {DIGITALOCEAN_KEY}",
                "Content-Type": "application/json",
            },
            json=req,
        )
        logger.info(response.json())
        droplet_id = response.json()["droplet"]["id"]

        # wait for IP address
        logger.info(f"Created {name} droplet_id {droplet_id}, waiting for IP...")
        ip = None
        while True:
            response = requests.get(
                f"{DROPLET_ENDPOINT}/{droplet_id}",
                headers={
                    "Authorization": f"Bearer {DIGITALOCEAN_KEY}",
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
            time.sleep(1)

        port = random.randint(PROXY_PORT_MIN, PROXY_PORT_MAX)
        proxy = client.create(
            "proxies",
            {
                "uuid": proxy_uuid,
                "address": f"{ip}:{port}",
                "description": name,
                "state": "CREATING",
                "failure_count": 0,
                "metadata": {
                    "provider": "digitalocean",
                    "region": region,
                    "droplet_id": droplet_id,
                },
            }
        )

        with tempfile.NamedTemporaryFile() as tmp_key:
            tmp_key.write(PROXY_SSH_KEY)
            tmp_key.flush()

            # logger.info(f"IP is {ip}, waiting for machine to come up...")
            # time.sleep(60)

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            while True:
                try:
                    logger.info(f"Connecting to {ip} via SSH...")
                    ssh.connect(ip, username="root", key_filename=tmp_key.name, timeout=10)
                    break
                except:
                    logger.info("Waiting a bit...")
                    time.sleep(5)

            logger.info("Writing systemd unit...")
            stdin_, stdout_, stderr_ = ssh.exec_command(
                "cat >/etc/systemd/system/microsocks.service"
            )
            stdin_.write(UNITFILE.format(port=port))
            stdin_.close()
            stdout_.channel.recv_exit_status()

            for cmd in SETUP:
                stdin_, stdout_, stderr_ = ssh.exec_command(cmd)
                stdout_.channel.recv_exit_status()
                lines = stdout_.readlines()
                logger.info(f"{cmd}: {lines}")

        proxy["state"] = "UP"

        client.update("proxies", proxy["uuid"], proxy)
        logger.info(f"Created proxy {proxy}")

    @classmethod
    def remove_droplet(cls, droplet_id):
        logger.info(f"Removing droplet {droplet_id}")
        response = requests.delete(
            f"{DROPLET_ENDPOINT}/{droplet_id}/destroy_with_associated_resources/dangerous",
            headers={
                "Authorization": f"Bearer {DIGITALOCEAN_KEY}",
                "Content-Type": "application/json",
                "X-Dangerous": "true",
            },
        )

    @classmethod
    def remove_proxy(cls, proxy):
        logger.info(f"Removing proxy {proxy}")
        cls.remove_droplet(proxy["metadata"].get("droplet_id"))

    @classmethod
    def get_proxies_by_name(cls):
        r = {}
        nexturl = DROPLET_ENDPOINT
        while nexturl:
            response = requests.get(
                nexturl,
                headers={
                    "Authorization": f"Bearer {DIGITALOCEAN_KEY}",
                    "Content-Type": "application/json",
                },
            )
            for droplet in response.json().get("droplets", []):
                if PROXY_TAG in droplet["tags"]:
                    r[droplet["name"]] = droplet
            nexturl = response.json().get("links", {}).get("pages", {}).get("next")
        return r

    @classmethod
    def cleanup(cls, client):
        logger.info("Cleanup enumerating digitalocean proxies...")
        stray = cls.get_proxies_by_name()
        logger.info(f"Found {len(stray)} running proxies under tag {PROXY_TAG}")
        creating_cutoff = (datetime.datetime.utcnow().replace(
            tzinfo=datetime.timezone.utc
        ) - datetime.timedelta(minutes=10)).isoformat()

        bad_proxies = []
        for proxy in client.list('proxies'):
            if proxy["description"] in stray:
                if proxy["state"] == "DOWN":
                    # we should delete this
                    logger.info(f"Proxy {proxy} marked Down")
                elif (
                        proxy["state"] == "CREATING"
                        and proxy["modified_at"] < creating_cutoff
                ):
                    # delete
                    logger.info(f"Proxy {proxy} has been Creating for too long")
                    client.delete('proxies', proxy["uuid"])
                else:
                    # keep
                    del stray[proxy["description"]]
            else:
                if proxy["state"] != "DOWN":
                    logger.info(f"No droplet for proxy {proxy}, marking Down")
                    proxy["state"] = "DOWN"
                    client.update('proxies', proxy["uuid"], proxy)

        for name, info in stray.items():
            if not name.startswith(PROXY_PREFIX):
                continue
            logger.info(f"Removing stray droplet {name} {info['id']}")
            cls.remove_droplet(info["id"])
        logger.info("Cleanup done")
