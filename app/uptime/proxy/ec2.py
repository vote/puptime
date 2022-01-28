import datetime
import logging
import random
import uuid

from django.conf import settings

from common import enums
from common.aws import get_proxy_ec2_client
from common.util import safe_while
from uptime.models import Proxy


"""
    "eu-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-south-1",
    "eu-west-3",
    "eu-north-1",
    "ap-northeast-2",
    "ap-northeast-3",
    "ap-northeast-1",
""",


logger = logging.getLogger("uptime")


class EC2Proxy(object):
    @classmethod
    def create(cls):
        from uptime.proxy.common import create_ubuntu_proxy

        region = random.choice(list(settings.EC2_PROXY_REGIONS.keys()))
        ec2_client = get_proxy_ec2_client(region)

        ami = settings.EC2_PROXY_REGIONS[region]["ami"]
        subnet_id = settings.EC2_PROXY_REGIONS[region]["subnet_id"]
        instance_type = settings.EC2_PROXY_REGIONS[region]["instance_type"]

        proxy_uuid = uuid.uuid4()
        name = f"proxy-ec2-{region}-{str(proxy_uuid)}"

        response = ec2_client.run_instances(
            ImageId=ami,
            InstanceType=instance_type,
            KeyName=settings.AWS_PROXY_KEY_NAME,
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "uptime", "Value": settings.PROXY_TAG,},],
                },
            ],
            NetworkInterfaces=[
                {
                    "AssociatePublicIpAddress": True,
                    "DeviceIndex": 0,
                    "SubnetId": subnet_id,
                }
            ],
            #            InstanceMarketOptions={
            #                "MarketType": "spot",
            #                "SpotOptions": {
            #                    "SpotInstanceType": "one-time",
            #                    "InstanceInterruptionBehavior": "terminate",
            #                },
            #            },
        )
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 200:
            logger.error(f"Failed to create {name}")
            return
        i = response["Instances"][0]
        instance_id = i["InstanceId"]
        logger.info(f"Created instance {instance_id} in {region}")

        with safe_while(sleep=5, tries=30) as proceed:
            while proceed():
                logger.info("Waiting for public IP address...")
                try:
                    response = ec2_client.describe_instances(InstanceIds=[instance_id])
                    ip = response["Reservations"][0]["Instances"][0].get(
                        "PublicIpAddress"
                    )
                    if ip:
                        break
                except Exception as e:
                    logger.info(e)

        create_ubuntu_proxy(
            "ec2", region, name, ip, {"region": region, "instance_id": instance_id,}, "ubuntu",
        )

    @classmethod
    def remove_instance(cls, region, instance_id):
        ec2_client = get_proxy_ec2_client(region)
        ec2_client.terminate_instances(InstanceIds=[instance_id],)

    @classmethod
    def remove_proxy(cls, proxy):
        logger.info(f"Removing proxy {proxy}")
        cls.remove_instance(
            proxy.metadata.get("region"), proxy.metadata.get("instance_id")
        )

    @classmethod
    def get_proxies(cls):
        r = {}
        for region in settings.EC2_PROXY_REGIONS.keys():
            logger.info(f"Enumerating ec2 instances in {region}...")
            ec2_client = get_proxy_ec2_client(region)
            response = ec2_client.describe_instances(
                Filters=[
                    {"Name": "tag:uptime", "Values": [settings.PROXY_TAG],},
                    {
                        "Name": "instance-state-name",
                        "Values": [
                            "running",
                            "pending",
                            "shutting-down",
                            "stopping",
                            "stopped",
                        ],
                    },
                ],
                MaxResults=1000,
            )
            for res in response.get("Reservations", []):
                for i in res.get("Instances", []):
                    i["Region"] = region
                    r[i["InstanceId"]] = i
        return r

    @classmethod
    def cleanup(cls):
        logger.info("Cleanup enumerating ec2 proxies...")
        stray = cls.get_proxies()
        logger.info(
            f"Found {len(stray)} non-terminated proxies under tag uptime:{settings.PROXY_TAG}"
        )
        creating_cutoff = datetime.datetime.utcnow().replace(
            tzinfo=datetime.timezone.utc
        ) - datetime.timedelta(minutes=10)

        for proxy in Proxy.objects.filter(source="ec2"):
            if proxy.metadata.get("instance_id") in stray:
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
                    logger.info(f"Proxy {proxy} - keeping for now")
                    del stray[proxy.metadata.get("instance_id")]
            else:
                if proxy.status != enums.ProxyStatus.DOWN:
                    logger.info(f"No instance for proxy {proxy}, marking Down")
                    proxy.status = enums.ProxyStatus.DOWN
                    proxy.save()

        for instance_id, info in stray.items():
            logger.info(f"Removing stray instance {instance_id}")
            r = cls.remove_instance(info["Region"], instance_id)
            logger.info(r)
        logger.info("Cleanup done")
