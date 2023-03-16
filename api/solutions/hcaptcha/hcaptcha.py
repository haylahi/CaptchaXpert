from ..common import *
from .precompiled_solution import hcaptcha
import logging

from ..exceptions import MaxRetryExceededException

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [HcaptchaChallenger] - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class Hcaptcha(Selenium):
    def __init__(self, host, driver, wait, hook_frames, challenge_frames, storage, image_getting_method,
                 next_locator, callback_at, callback_module, *args, **kwargs):
        super().__init__()
        self.HOST = host
        self.driver = driver
        self.wait = wait

        self.HOOK_FRAME = None
        self.HOOK_FRAMES = hook_frames
        self.CHALLENGE_FRAME = None
        self.CHALLENGE_FRAMES = challenge_frames

        self.storage = storage
        self.image_getting_method = image_getting_method
        self.hcaptcha_challenger = hcaptcha
        self.next_locator = next_locator
        if self.next_locator is None:
            self.next_locator = lambda: 1 == 2

        self.callback_at = callback_at
        self.callback_module = callback_module

        self.args = args
        self.kwargs = kwargs

    def anti_checkbox(self):
        """ Click checkbox and return True else False """

        self.driver.switch_to.frame(self.HOOK_FRAME)
        try:
            self.driver.find_element(By.XPATH, '//*[@id="anchor-tc"]')
        except Selenium.__exceptions__:
            return False
        else:
            self.click_js((By.ID, "checkbox"))
            return True
        finally:
            self.driver.switch_to.parent_frame()

    def is_label_visible(self):
        """Check whether label visible or not"""

        for i, f in enumerate(self.CHALLENGE_FRAMES):
            self.driver.switch_to.frame(f)
            try:
                self.driver.find_element(By.CLASS_NAME, 'prompt-text')
            except NoSuchElementException:
                pass
            else:
                return True
            finally:
                self.driver.switch_to.parent_frame()
            if i == len(self.CHALLENGE_FRAMES) - 1:
                return False

    def is_challenge_solved(self):
        """Check whether challenge solved or not"""
        try:
            return self.HOOK_FRAME.get_attribute('data-hcaptcha-response') != ''
        except Selenium.__exceptions__:
            return False

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

    def callback_solving(self):
        logger.debug("[CallBacks] Using 2captcha callback")
        site_key = self.driver.find_element(By.XPATH, '//*[@data-sitekey]').get_attribute('data-sitekey')
        solver = self.twocaptcha.TwoCaptcha('<your-twocaptcha-api>')  # noqa
        result = solver.hcaptcha(site_key, self.driver.current_url)
        response = result['code']
        self.driver.execute_script(f"arguments[0].setAttribute('data-hcaptcha-response', '{response}');", self.HOOK_FRAME)
        logger.debug("[CallBacks] Token injected!")

    def _solve(self, retries=10):
        challenger = self.hcaptcha_challenger.new_challenger(self.HOST, self.driver, self.HOOK_FRAME, self.CHALLENGE_FRAME,
                                                             self.next_locator, self.image_getting_method,
                                                             debug=True, dir_workspace=self.storage)
        for r in range(retries):
            try:
                if (_resp := challenger.anti_hcaptcha()) is None:
                    continue
                if _resp == challenger.CHALLENGE_SUCCESS:
                    return challenger.utils.get_hcaptcha_response(self.driver)
            except self.hcaptcha_challenger.exceptions.ChallengePassed:
                return challenger.utils.get_hcaptcha_response(self.driver)
            challenger.utils.refresh(self.driver)
            logger.debug(f"Retrying challenge...")
            self.delay.custom(1)

            if self.callback_module is not None:
                if r == self.callback_at + 1:
                    raise MaxRetryExceededException
                if r == self.callback_at:
                    self.callback_solving()
                    return True

        return False

    def solve(self) -> bool:  # noqa
        """Face hcaptcha gracefully using ml models as classifiers"""

        self.real_hook_frame()
        response = False
        response_id = multiWait(self.driver, [self.anti_checkbox, self.is_label_visible, self.is_challenge_solved, self.next_locator], 30)
        if response_id == 0:
            response_id = multiWait(self.driver, [lambda: 1 == 2, self.is_label_visible, self.is_challenge_solved, self.next_locator], 30)
        if response_id == 1:
            self.real_challenge_frame()
            if self._solve():
                response = True
        else:
            response = True

        return response
