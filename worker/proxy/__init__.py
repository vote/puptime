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

PROXY_TARGET = int(os.getenv("PROXY_TARGET", 5))

logger = logging.getLogger("proxy")


PROXY_TYPES = [
    digitalocean.DigitalOceanProxy
]

def cleanup(client):
    for cls in PROXY_TYPES:
        cls.cleanup(client)
        
def check_health(client):
    pass

def create_proxies(client, cls):
    proxies = client.list('proxies')
    num_up = 0
    for proxy in proxies:
        if proxy["state"] == "Up":
            num_up += 1

    if num_up < PROXY_TARGET:
        want = PROXY_TARGET - num_up
        logger.info(f"Have {num_up}/{PROXY_TARGET}, creating {want}")
        for i in range(want):
            cls.create(client)
