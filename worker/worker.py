import argparse
import sys
import logging
import os
from client import UptimeClient
import dotenv

dotenv.load_dotenv()
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

parser = argparse.ArgumentParser(description='Monitor some things')
parser.add_argument('command', help='Command')

args = parser.parse_args()

c = UptimeClient()

if args.command == 'check-proxies':
    import proxy
    proxy.cleanup(c)
elif args.command == 'create-proxies':
    import proxy
    proxy.create_proxies(c, proxy.DigitalOceanProxy)
elif args.command == 'check-all':
    import check
    check.check_all(c)

"""    
sites = c.list('sites')
proxies = c.list('proxies')

if True:
    s = c.create(
        'sites',
        {
            'url': 'http://foo.com',
            'description': "asdf",
        }
    )

import proxy
proxy.DigitalOceanProxy.create(c)
proxy.DigitalOceanProxy.cleanup(c)
proxy.create_proxies(c, proxy.DigitalOceanProxy)

"""
