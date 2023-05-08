import logging
import os
import shutil
import time
import uuid
from typing import Any

from .solutions.exceptions import InvalidCaptchaTypeException
from .solutions.common import *

logger = logging.getLogger(__name__)


def preprocess(func):
    """
    Create temporary storage for captcha solving
    Handle some common captcha exceptions
    """

    def wrapper(self, *args, **kwargs):
        self.CHALLENGE_RUNNING = True
        self.create_storage() if self.make_storage else ''

        try:
            return func(self, *args, **kwargs)
        except (UnexpectedAlertPresentException, StaleElementReferenceException, TimeoutException):
            return False
        except Exception as e:
            raise e
        finally:
            if self.driver is not None:
                self.driver.switch_to.parent_frame()
            if self.make_storage:
                self.destroy_storage() if self.destroyer else ''

    return wrapper


class CaptchaSolver(Selenium):
    """Face common captchas gracefully"""

    ACTIVE_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
    TEMP_STORAGE_PREFIX = os.path.join(ACTIVE_DIRECTORY, 'temp_cache')

    def __init__(self, driver=None, timeout=60, destroy_storage=True, make_storage=True, make_storage_at=None,
                 image_getting_method='screenshot', callback_at: int = None, host='http://127.0.0.1:5000',
                 hook_frame=None, challenge_frame=None, response_locator=None):
        """
        CaptchaSolver api for selenium webdriver
        :param driver: selenium webdriver object
        :param timeout: webdriver wait
        :param destroy_storage: destroy temp storage after processing captcha
        :param make_storage: make temp storage for captcha data during runtime
        :param make_storage_at: storage location
        :param image_getting_method: either "screenshot" or "request"
        :param callback_at: when to do callback to paid captcha solving service, int
        :param host: captcha images solver host, default: http://127.0.0.1:5000
        :param hook_frame: custom hook frame in case of multiple captchas on single page
        :param challenge_frame: custom challenge frame in case of multiple captchas on single page
        :param response_locator: consider captcha solved as soon as possible this locator found
        """

        super().__init__()
        self.HOST = host
        self.CHALLENGE_RUNNING = False
        self.RESPONSE = None

        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(self.driver, self.timeout)
        self.type = None

        self.storage = None
        self.make_storage = make_storage
        self.make_storage_at = make_storage_at
        self.destroyer = destroy_storage

        self.next_locator = None
        self.image_getting_method = image_getting_method

        self.callback_at = callback_at
        self.callback_module = None
        if self.callback_at is not None:
            import twocaptcha
            self.callback_module = twocaptcha

        self.response_locator = response_locator
        self._HOOK_FRAME = hook_frame
        self._CHALLENGE_FRAME = challenge_frame
        self.HOOK_FRAME = None
        self.HOOK_FRAMES = None
        self.CHALLENGE_FRAME = None
        self.CHALLENGE_FRAMES = None

        # Required modules
        self.recaptcha_v2 = None
        self.recaptcha_v3 = None
        self.recaptcha_audio = None
        self.hcaptcha = None
        self.antibot = None
        self.gpcaptcha = None

    def setCaptchaTypeAsHcaptcha(self):
        self.type = 'hcaptcha'
        from .solutions.hcaptcha import hcaptcha
        self.hcaptcha = hcaptcha
        return self

    def setCaptchaTypeAsGpCaptcha(self):
        self.type = 'gp_captcha'
        from .solutions.gpcaptcha import gpcaptcha
        self.gpcaptcha = gpcaptcha
        return self

    def setCaptchaTypeAsRecaptchaV2(self):
        self.type = 'recaptcha_v2'
        from .solutions.recaptcha import recaptcha_v2
        self.recaptcha_v2 = recaptcha_v2
        return self

    def setCaptchaTypeAsRecaptchaV3(self):
        self.type = 'recaptcha_v3'
        from .solutions.recaptcha import recaptcha_v3
        self.recaptcha_v3 = recaptcha_v3
        return self

    def setCaptchaTypeAsAntiBotLinks(self):
        self.type = 'antibot_links'
        from .solutions.antibot import antibot
        self.antibot = antibot
        return self

    def setCaptchaTypeAsNewCaptcha(self):
        self.type = "new_captcha"
        return self

    def create_storage(self):
        """Create temporary storage"""
        if self.make_storage_at is None:
            self.make_storage_at = os.path.join(os.path.dirname(__file__), "temp_cache")
        self.storage = os.path.join(self.make_storage_at, str(uuid.uuid4()))
        os.makedirs(self.storage)

    def destroy_storage(self):
        """Destroy temporary storage"""
        shutil.rmtree(self.storage, ignore_errors=True)

    def find_frames(self, secs: float or int = None, exception=False):
        """Find frames for recaptcha and hcaptcha"""
        xpaths = [
            '//iframe[@title="Widget containing checkbox for hCaptcha security challenge"]',
            '//iframe[@title="Main content of the hCaptcha challenge"]',
            '//iframe[@title="reCAPTCHA"]',
            '//iframe[contains(@title, "recaptcha")]',
            '//iframe[@title="reCAPTCHA" and contains(@src, "invisible")]'
        ]
        locs = [(By.XPATH, x) for x in xpaths]
        if secs is None:
            secs = self.timeout
        try:
            multiWait(self.driver, locs, secs)
        except TimeoutException as e:
            if exception:
                raise e
            return None

        HCAPTCHA_HOOK_FRAME = locs[0]
        HCAPTCHA_CHALLENGE_FRAME = locs[1]
        RECAPTCHA_HOOK_FRAME = locs[2]
        RECAPTCHA_CHALLENGE_FRAME = locs[3]
        RECAPTCHA_V3_FRAME = locs[4]

        for i in range(self.timeout):
            if self.type == 'recaptcha_v3':
                self.HOOK_FRAME = self.find_element(*RECAPTCHA_V3_FRAME)
                if self.HOOK_FRAME not in (None, []):
                    return True
            else:
                if self.type == 'hcaptcha':
                    self.HOOK_FRAMES = self.find_elements(*HCAPTCHA_HOOK_FRAME)
                    self.CHALLENGE_FRAMES = self.find_elements(*HCAPTCHA_CHALLENGE_FRAME)
                else:
                    self.HOOK_FRAMES = self.find_elements(*RECAPTCHA_HOOK_FRAME)
                    self.CHALLENGE_FRAMES = self.find_elements(*RECAPTCHA_CHALLENGE_FRAME)

                if self.HOOK_FRAMES not in (None, []) and self.CHALLENGE_FRAMES not in (None, []):
                    return True
            self.delay.custom(1)
        raise Exception('NoSuchFrameFound -> HOOK_FRAME and CHALLENGE_FRAME cannot be none')

    def autoType(self, secs: float or int = None, exception=False):
        xpaths = ['//iframe[@title="Widget containing checkbox for hCaptcha security challenge"]',
                  '//iframe[@title="Main content of the hCaptcha challenge"]',
                  '//iframe[@title="reCAPTCHA"]',
                  '//iframe[contains(@title, "recaptcha")]', ]
        locs = [(By.XPATH, x) for x in xpaths]
        if secs is None:
            secs = self.timeout
        try:
            ID = multiWait(self.driver, locs, secs)
        except TimeoutException as e:
            if exception:
                raise e
            return None
        self.setCaptchaTypeAsHcaptcha() if ID in (0, 1) else self.setCaptchaTypeAsRecaptchaV2()
        return True

    def new_captcha(self, *args, **kwargs) -> Any:
        """Implement new type of captcha that is not supported by original class"""
        pass

    @preprocess
    def auto_solve(self):  # Real signature in ExpandAI
        """
        This works like an extension::
            This will look for recaptcha or hcaptcha frames every n second and also solve it

            *Note*: Run this in thread as it will run unless main program exit
        :return bool
        """
        pass

    @preprocess
    def solve(self, *args, **kwargs) -> bool:
        """
        Solve any captcha of type selected using setTypeAs...method
        :param args: Any argument to parse
        :param kwargs: Any kwargs to parse
        :return: response
        """

        assert self.driver is not None, "Driver must not be of NoneType!"
        start_time = time.time()
        logger.info(f"[CaptchaSolver] Solving {self.type}")
        self.next_locator = kwargs.get('next_locator')

        # If type is frames captcha
        # Enter frame -> process captcha -> Exit frame
        if self.type in ("hcaptcha", "recaptcha_v2", 'recaptcha_v3'):
            if self._HOOK_FRAME is None:
                self.find_frames(exception=True)
            else:
                self.HOOK_FRAMES = [self._HOOK_FRAME]
                self.CHALLENGE_FRAMES = [self._CHALLENGE_FRAME]
            if self.type == 'recaptcha_v2':
                self.RESPONSE = self.recaptcha_v2.RecaptchaV2(self.HOST, self.driver, self.wait, self.timeout,
                                                              self.HOOK_FRAMES,
                                                              self.CHALLENGE_FRAMES, self.storage, self.image_getting_method,
                                                              self.next_locator, self.callback_module, self.callback_at,
                                                              self.response_locator,
                                                              *args, **kwargs).solve()
            elif self.type == 'recaptcha_v3':
                self.RESPONSE = self.recaptcha_v3.RecaptchaV3().solve()
            elif self.type == 'hcaptcha':
                self.RESPONSE = self.hcaptcha.Hcaptcha(self.HOST, self.driver, self.wait, self.HOOK_FRAMES,
                                                       self.CHALLENGE_FRAMES, self.storage, self.image_getting_method,
                                                       self.next_locator, self.callback_module, self.callback_at,
                                                       *args, **kwargs).solve()

        elif self.type == "antibot_links":
            self.RESPONSE = self.antibot.AntiBotLinks(self.HOST, self.driver, self.wait, self.storage, *args, **kwargs).solve()
        elif self.type == 'gp_captcha':
            self.RESPONSE = self.gpcaptcha.GpCaptcha(self.driver, self.wait, self.timeout).solve()
        elif self.type == "new_captcha":
            self.RESPONSE = self.new_captcha(*args, **kwargs)
        else:
            raise InvalidCaptchaTypeException

        logger.info(f"[CaptchaSolver] Type: {self.type} | Returned: {self.RESPONSE} |"
                    f" Time consumed {round(time.time() - start_time, 3)} seconds")
        return self.RESPONSE
