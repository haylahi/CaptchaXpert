import logging
import random

import requests

from ..common import *
from ..exceptions import InvalidImageGettingMethodException, MaxRetryExceededException

logger = logging.getLogger(__name__)

__all__ = ['RecaptchaUtils', 'Selenium', 'safe_request', 'By', 'NoSuchElementException']


class RecaptchaUtils(Selenium):

    def __init__(self, host, driver, wait, timeout, hook_frames, challenge_frames, storage, image_getting_method, next_locator,
                 callback_module, callback_at, response_locator, *args, **kwargs):
        """
        Recaptcha solving
        :param host: Captcha solver server complete address like http://127.0.0.1:5000
        :param driver: WebDriver object
        :param wait: WebDriverWait object
        :param hook_frames: list of hook frames
        :param challenge_frames: list of challenge frames
        :param storage: storage path
        :param image_getting_method: screenshot or request
        :param next_locator: possible next locator, useful in solving invisible captcha
        :param callback_module: use your own callback module, like 2captcha
        :param callback_at: when to use callback, like after 5 retries
        """

        self.HOST = host
        self.driver = driver
        self.wait = wait
        self.timeout = timeout
        self.next_locator = next_locator
        if self.next_locator is None:
            self.next_locator = lambda: 1 == 2

        self.HOOK_FRAME = None
        self.CHALLENGE_FRAME = None
        self.HOOK_FRAMES = hook_frames
        self.CHALLENGE_FRAMES = challenge_frames

        self.storage = storage
        self.image_getting_method = image_getting_method
        self.count_retry = 0
        self.callback_at = callback_at
        self.response_locator = response_locator

        # Additional modules
        self.callback_module = callback_module

        self.args = args
        self.kwargs = kwargs
        super().__init__(self.driver, self.wait, self.timeout)

    def anti_checkbox(self):
        """ Click checkbox and return True else False """

        self.driver.switch_to.frame(self.HOOK_FRAME)
        try:
            checkbox = self.driver.find_element(By.XPATH, '//*[@id="rc-anchor-container"]')
        except Selenium.__exceptions__:
            return False
        else:
            self.click_js(checkbox)
            logger.debug("Clicked checkbox")
            return True
        finally:
            self.driver.switch_to.parent_frame()

    def recaptcha_response(self) -> bool:
        """Check whether recaptcha solved or not"""
        try:
            if self.response_locator is not None:
                return self.driver.find_element(*self.response_locator).get_attribute('value') != ''
            for elem in self.driver.find_elements(By.XPATH, '//*[@name="g-recaptcha-response"]'):
                if elem.get_attribute('value'):
                    return True
            return False
        except Selenium.__exceptions__:
            return False

    def _is_banner_visible(self, _frame):
        """Check if label banner visible on given frame"""

        self.driver.switch_to.frame(_frame)
        try:
            self.driver.find_element(By.XPATH, '//strong')
        except Selenium.__exceptions__:
            try:
                self.driver.find_element(By.ID, 'audio-instructions')
            except Selenium.__exceptions__:
                return False
            else:
                return True
        else:
            return True
        finally:
            self.driver.switch_to.parent_frame()

    def is_banner_visible(self):
        """Check if label banner visible on any frame"""

        for f in self.CHALLENGE_FRAMES:
            if self._is_banner_visible(f):
                logger.debug("Label banner is visible")
                return True
        return False

    def reload_captcha(self) -> None:
        """Just press the retry button"""
        logger.debug("Reloading captcha...")
        self.driver.execute_script('document.getElementById("recaptcha-reload-button").click()')

    def verify_captcha(self) -> None:
        """Just press the verify button"""
        logger.debug("Verifying captcha...")
        self.click_js((By.ID, 'recaptcha-verify-button'))

    def callback_solving(self):
        """Feature to use any callbacks like 2captcha, nopecha, etc"""
        logger.debug("[CallBacks] Using 2captcha callback")
        site_key = self.driver.find_element(By.XPATH, '//*[@data-sitekey]').get_attribute('data-sitekey')
        two_solver = self.callback_module.TwoCaptcha('<your-twocaptcha-api>')
        result = two_solver.recaptcha(site_key, self.driver.current_url)
        response = result['code']
        self.driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML = "{response}";')
        logger.debug("[CallBacks] Token injected!")

    def retry_challenge(self):
        """Switch to parent frame and retry challenge"""

        logger.debug(f"Retrying...")
        self.reload_captcha()
        self.driver.switch_to.parent_frame()
        self.delay.custom(3)

        # Back calls implementation
        if self.callback_at is not None:
            self.count_retry += 1
            if self.count_retry == self.callback_at + 1:
                raise MaxRetryExceededException
            if self.count_retry == self.callback_at:
                self.callback_solving()
                return True

        return self._solve()

    def is_retry_prompt(self) -> bool:
        """Check if any retry prompt is visible"""

        self.driver.switch_to.frame(self.CHALLENGE_FRAME)
        try:
            elms = [x.is_displayed() for x in
                    self.driver.find_elements(By.XPATH, '//*[contains(text(), "Please")]')]
        except (NoSuchElementException, StaleElementReferenceException):
            pass
        else:
            logger.debug("Retry prompt found")
            return bool(True in elms)
        finally:
            self.driver.switch_to.parent_frame()

    def wait_till_new_images(self, xpaths, srcs):
        """Dynamically wait until new images load"""

        logger.debug("Waiting until new images load")
        for _ in range(100):
            try:
                if not [1 for xpath in xpaths if self.driver.find_element(By.XPATH, xpath).get_attribute('src') in srcs]:
                    logger.debug("All new images loaded")
                    return True
            except StaleElementReferenceException:
                pass
            self.delay.custom(0.1)
        return False

    def get_image_as_base64(self, image_element, callback):
        """Get image as base64 format"""

        logger.debug("Getting image in base64 format")
        if self.image_getting_method == 'request':
            img_path = f"{self.storage}/img.png"
            safe_request(image_element.get_attribute('src'), None, ConnectionError, on_error=callback, image_path=img_path)
            img_as_base64 = path_to_base64(img_path, encoding='ascii')
        elif self.image_getting_method == 'screenshot':
            try:
                img_as_base64 = image_element.screenshot_as_base64
            except ElementClickInterceptedException:
                img_path = f"{self.storage}/img.png"
                safe_request(image_element.get_attribute('src'), None, ConnectionError, on_error=callback, image_path=img_path)
                img_as_base64 = path_to_base64(img_path, encoding='ascii')
        else:
            raise InvalidImageGettingMethodException(f"Unknown method {self.image_getting_method}\n"
                                                     " choose `request` or `screenshot`")

        logger.debug("Success getting image in base64 format")
        return img_as_base64

    def mark_images(self, response: requests.Response, image_wrappers, callback):
        """Mark images and update return their sources"""

        res = response.json()['response']
        if not res or True not in res:
            logger.debug("Bad response.")
            return callback()

        idx = indexN(res, True, 3)
        random.shuffle(idx)
        old_srcs = []
        for i in idx:
            wrapper = image_wrappers[f'wrapper-{i}']['element']
            old_srcs.append(wrapper.get_attribute('src'))
            self.click_js(wrapper)
            image_wrappers[f'wrapper-{i}']['marked'] = True
            self.delay.one10_one()
            logger.debug(f"Marked {i}th image")

        return old_srcs

    def mark_new_images(self, response: requests.Response, image_wrappers):
        """Mark new images and update return their sources"""

        res = response.json()['response']
        if not res or True not in res:
            return True

        old_srcs = []
        idx = indexN(res, True, 3)
        random.shuffle(idx)
        for i in idx:
            wrapper = image_wrappers[list(image_wrappers.keys())[i]]['element']
            old_srcs.append(wrapper.get_attribute('src'))
            self.click_js(wrapper)
            image_wrappers[list(image_wrappers.keys())[i]]['marked'] = True
            self.delay.one10_one()

        return old_srcs

    def real_hook_frame(self):
        """Choose only hook frame that is currently visible"""

        logger.debug("Finding real hook frame")
        if len(self.HOOK_FRAMES) == 1:
            self.HOOK_FRAME = self.HOOK_FRAMES[0]
        else:
            self.HOOK_FRAME = [f for f in self.HOOK_FRAMES if f.is_displayed()][0]
        logger.debug("Real hook frame found")

    def real_challenge_frame(self):
        """Choose only challenge frame that is currently visible, timeout at 15 seconds"""

        logger.debug("Finding real challenge frame")
        if len(self.CHALLENGE_FRAMES) == 1:
            self.CHALLENGE_FRAME = self.CHALLENGE_FRAMES[0]
        else:
            timeout = 15
            for i in range(timeout):
                if len([f for f in self.CHALLENGE_FRAMES if f.is_displayed()]) != 0:
                    break
                elif i == timeout - 1:
                    raise TimeoutException

                self.delay.custom(1)

            self.CHALLENGE_FRAME = [f for f in self.CHALLENGE_FRAMES if f.is_displayed()][0]
        logger.debug("Real challenge frame found")

    def _solve(self) -> bool:
        pass

    def solve(self):
        pass
