import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

from .tools.pre_processing import pstrings
from .tools.templates.selenium_ import Selenium

import requests

from .harvester import Harvester, CaptchaKindEnum
from .captchasolver import CaptchaSolver

ACTIVE_PORTS = [5000, 5001, 5002, 5003]
logger = logging.getLogger(__name__)
hcaptcha_solver = CaptchaSolver().setCaptchaTypeAsHcaptcha()
recaptcha_solver = CaptchaSolver().setCaptchaTypeAsRecaptchaV2()
pool = ThreadPoolExecutor()


def get_free_port(rmin=49152, rmax=65535):
    while True:
        nport = random.randint(rmin, rmax)
        if nport not in ACTIVE_PORTS:
            ACTIVE_PORTS.append(nport)
            return nport


class TokenAPI(Selenium):
    def __init__(self, captcha_type, url, data_sitekey, driver='uc', proxy=None, timeout=120):
        self.host = '127.0.0.1'
        self.port = get_free_port()
        self.domain = pstrings.Grep(url).domain()
        self.site_key = data_sitekey
        self.harvester_server = None
        self.type = captcha_type
        self.timeout = timeout
        if self.type == 'recaptcha':
            self.type += '-v2'

        self.init_server()
        host_rules = f'MAP {self.domain} {self.host}:{self.port}'
        super().__init__(webdriver_=driver, proxy_server=proxy, headless2=False, timeout=timeout,
                         args=(f'--host-rules={host_rules}', ), start=True)
        hcaptcha_solver.driver = recaptcha_solver.driver = self.driver
        hcaptcha_solver.wait = recaptcha_solver.wait = self.wait

    def init_server(self):
        harvester_server = Harvester(host=self.host, port=self.port)
        harvester_server._intercept(self.domain, self.site_key, CaptchaKindEnum(self.type)) # noqa
        self.harvester_server = harvester_server

        server_thread = Thread(target=harvester_server.serve, daemon=True)
        server_thread.start()
        logger.info(f"Serving harvester on http://{self.host}:{self.port}")

    def shutdown_server(self):
        self.harvester_server.httpd.shutdown()
        logger.info(f"Shutdown harvester from http://{self.host}:{self.port}")

    def error_handler(func, *args, **kwargs):    # noqa
        def wrapper(self, *args, **kwargs): # noqa
            try:
                res = func(self)  # noqa
            except Exception as e:
                logger.error(e, exc_info=True)
            else:
                return res
            finally:
                self.shutdown_server()
                self.is_running.clear()
                self.quit()
        return wrapper

    def _fetch_token(self):
        logger.info("Making Token")
        try:
            self.get(f"http://{self.domain}")
            captcha_solver = recaptcha_solver if self.type == 'recaptcha-v2' else hcaptcha_solver
            while True:
                if captcha_solver.solve() or requests.get(f"http://{self.host}:{self.port}/{self.domain}/tokens").json():
                    return requests.get(f"http://{self.host}:{self.port}/{self.domain}/tokens").json()[0]
                else:
                    self.driver.refresh()
        except Selenium.__exceptions__:
            return False

    @error_handler
    def fetch_token(self):
        future = pool.submit(self._fetch_token)
        for i in range(self.timeout):
            if future.done():
                return future.result()
            time.sleep(1)

        return 'TimeoutException'
