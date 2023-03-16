import logging
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

import requests
from webdriver_manager.chrome import ChromeDriverManager

from .captchasolver import CaptchaSolver
from .harvester import Harvester, CaptchaKindEnum
from .tools.common.driver import *
from .tools.pre_processing import pstrings

logger = logging.getLogger(__name__)
hcaptcha_solver = CaptchaSolver().setCaptchaTypeAsHcaptcha()
recaptcha_solver = CaptchaSolver().setCaptchaTypeAsRecaptchaV2()
pool = ThreadPoolExecutor()


def get_free_port():
    """
    Returns a free port number on localhost.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]


class TokenAPI:
    def __init__(self, captcha_type, url, data_sitekey, proxy=None, timeout=120):
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
        args = [f'--host-rules={host_rules}', '--headless=new']
        self.driver = create_driver(proxy, driver_executable_path=ChromeDriverManager().install(), arguments=args)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, timeout)
        hcaptcha_solver.driver = recaptcha_solver.driver = self.driver
        hcaptcha_solver.wait = recaptcha_solver.wait = self.wait

    def init_server(self):
        harvester_server = Harvester(host=self.host, port=self.port)
        harvester_server._intercept(self.domain, self.site_key, CaptchaKindEnum(self.type))  # noqa
        self.harvester_server = harvester_server

        server_thread = Thread(target=harvester_server.serve, daemon=True)
        server_thread.start()
        logger.info(f"Serving harvester on http://{self.host}:{self.port}")

    def shutdown_server(self):
        self.harvester_server.httpd.shutdown()
        logger.info(f"Shutdown harvester from http://{self.host}:{self.port}")

    def error_handler(func, *args, **kwargs):  # noqa
        def wrapper(self, *args, **kwargs):  # noqa
            try:
                res = func(self)  # noqa
            except Exception as e:
                logger.error(e, exc_info=True)
            else:
                return res
            finally:
                self.shutdown_server()
                self.driver.quit()

        return wrapper

    def _fetch_token(self):
        logger.info("Making Token")
        try:
            self.driver.get(f"http://{self.domain}")
            captcha_solver = recaptcha_solver if self.type == 'recaptcha-v2' else hcaptcha_solver
            while True:
                if captcha_solver.solve() or requests.get(f"http://{self.host}:{self.port}/{self.domain}/tokens").json():
                    return requests.get(f"http://{self.host}:{self.port}/{self.domain}/tokens").json()[0]
                else:
                    self.driver.refresh()
        except SELENIUM_EXCEPTIONS:
            return False

    @error_handler
    def fetch_token(self):
        future = pool.submit(self._fetch_token)
        for i in range(self.timeout):
            if future.done():
                return future.result()
            time.sleep(1)

        return 'TimeoutException'
