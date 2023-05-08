import logging
import socket
import time
from threading import Thread

import requests
from selenium.webdriver.support.wait import WebDriverWait
from seleniumbase import Driver

from .captchasolver import CaptchaSolver
from .harvester import Harvester, CaptchaKindEnum

logger = logging.getLogger(__name__)

from selenium.common.exceptions import (
    TimeoutException, ElementNotInteractableException, ElementNotVisibleException,
    ElementNotSelectableException, ElementClickInterceptedException, StaleElementReferenceException, NoSuchElementException,
    NoSuchAttributeException, JavascriptException, InvalidArgumentException, InvalidSelectorException, InvalidSessionIdException,
    NoSuchCookieException, NoSuchWindowException, NoSuchFrameException, NoAlertPresentException, UnexpectedAlertPresentException,
    MoveTargetOutOfBoundsException, WebDriverException
)

SELENIUM_EXCEPTIONS = (TimeoutException, ElementNotInteractableException, ElementNotVisibleException,
                       ElementNotSelectableException, ElementClickInterceptedException, StaleElementReferenceException,
                       NoSuchElementException,
                       NoSuchAttributeException, JavascriptException, InvalidArgumentException, InvalidSelectorException,
                       InvalidSessionIdException,
                       NoSuchCookieException, NoSuchWindowException, NoSuchFrameException, NoAlertPresentException,
                       UnexpectedAlertPresentException,
                       MoveTargetOutOfBoundsException, WebDriverException)


def get_free_port():
    """
    Returns a free port number on localhost.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]


class TokenAPI:
    def __init__(self, captcha_type, domain, data_sitekey, executor, proxy=None, timeout=120, visibility=False):
        self.host = '127.0.0.1'
        self.port = get_free_port()
        self.domain = domain
        self.site_key = data_sitekey
        self.harvester_server = None
        self.timeout = timeout
        self.executor = executor

        self.type = captcha_type
        if self.type == 'recaptcha':
            self.type += '-v2'

        self.init_server()

        host_rules = f'MAP {self.domain} {self.host}:{self.port}'
        args = [f'--host-rules={host_rules}']

        self.driver = Driver(uc=True, page_load_strategy='none', headless2=not visibility, proxy=proxy, extra_args=args)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, timeout)

        self.recaptcha_solver = CaptchaSolver(image_getting_method='screenshot').setCaptchaTypeAsRecaptchaV2()
        self.hcaptcha_solver = CaptchaSolver(image_getting_method='screenshot').setCaptchaTypeAsHcaptcha()
        self.hcaptcha_solver.driver = self.recaptcha_solver.driver = self.driver
        self.hcaptcha_solver.wait = self.recaptcha_solver.wait = self.wait

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
                res = func(self, *args, **kwargs)  # noqa
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
            captcha_solver = self.recaptcha_solver if self.type == 'recaptcha-v2' else self.hcaptcha_solver
            while True:
                if captcha_solver.solve() or requests.get(f"http://{self.host}:{self.port}/{self.domain}/tokens").json():
                    return requests.get(f"http://{self.host}:{self.port}/{self.domain}/tokens").json()[0]
                else:
                    self.driver.refresh()
        except SELENIUM_EXCEPTIONS:
            return 'WEBDRIVER_EXCEPTION'

    @error_handler
    def fetch_token(self, is_token_processed):
        future = self.executor.submit(self._fetch_token)
        for i in range(self.timeout):
            if is_token_processed.is_set():
                return 'TIMEOUT_EXCEPTION'
            if future.done():
                if future.result() == 'WEBDRIVER_EXCEPTION':
                    return future.result()
                elif future.result() is None:
                    return 'HARVESTER_EXCEPTION'
                else:
                    is_token_processed.set()
                    return f'Token-{future.result()}'
            time.sleep(1)

        return 'TIMEOUT_EXCEPTION'
