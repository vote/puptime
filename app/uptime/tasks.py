import logging

from celery import shared_task

from . import check, proxy

logger = logging.getLogger("uptime")


@shared_task
def tick():
    logger.info("tick")


@shared_task
def test():
    logger.info("test")


@shared_task
def check_proxies():
    proxy.check()


@shared_task
def check_all():
    check.check_all()
