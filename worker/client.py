import logging
import os
import requests

logger = logging.getLogger()


class UptimeClient(object):
    def __init__(self):
        self.base_url = f"{os.getenv('API_URL')}/v1/uptime"
        self.session = self.get_session()
        self.proxies = self.list('proxies')
        self.sites = self.list('sites')

    def get_session(self):
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry

        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(
            os.getenv('API_KEY'),
            os.getenv('API_SECRET')
        )
        session.mount(
            self.base_url,
            HTTPAdapter(
                max_retries=Retry(
                    total=1,
                    backoff_factor=1,
                    status_forcelist=[500, 502, 503, 504],
                    method_whitelist=["HEAD", "GET", "POST", "PUT"],
                )
            ),
        )
        return session

    def list(self, cls):
        next_url = f"{self.base_url}/{cls}/"
        r = []
        while next_url:
            response = self.session.get(next_url)
            r.extend(response.json().get('results'))
            next_url = response.json().get("next")
        return r

    def create(self, cls, data):
        response = self.session.post(f"{self.base_url}/{cls}/", data)
        logger.info(f"POST gets {response.json()}")
        return response.json()
    
    def update(self, cls, key, data):
        response = self.session.put(f"{self.base_url}/{cls}/{key}/", data)
        logger.debug(f"PUT gets {response.json()}")
        return response.json()

    def delete(self, cls, key):
        response = self.session.delete(f"{self.base_url}/{cls}/{key}/")
        #logger.debug(f"PUT delete {response.json()}")
        #return response.json()
