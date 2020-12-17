import logging
import os
from client import UptimeClient
import dotenv

dotenv.load_dotenv()
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

c = UptimeClient()
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

