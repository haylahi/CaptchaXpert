import logging

import requests

from .common import *

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [RecaptchaAudioChallenger] - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class RecaptchaAudio(RecaptchaUtils):

    def multiple_correct_prompt(self):
        self.driver.switch_to.frame(self.CHALLENGE_FRAME)
        try:
            error = self.driver.find_element(By.XPATH, '//*[contains(text(), "correct solutions required")]')
            if self.driver.find_element(By.ID, 'recaptcha-verify-button').get_attribute("disabled") == 'true':
                raise Exception
        except:
            return False
        else:
            return error.is_displayed()
        finally:
            self.driver.switch_to.parent_frame()

    def retry_prompt(self):
        self.driver.switch_to.frame(self.CHALLENGE_FRAME)
        try:
            elms = [x.is_displayed() for x in
                    self.driver.find_elements(By.XPATH, '//*[contains(text(), "Please")]')]
        except NoSuchElementException:
            pass
        else:
            return bool(True in elms)
        finally:
            self.driver.switch_to.parent_frame()

    def _solve(self) -> bool:
        """
        Use speech recognition to solve recaptcha
        This method is now deprecated because recaptcha easily classify chromedriver as bot using this
        """

        self.driver.switch_to.frame(self.CHALLENGE_FRAME)

        if self.multiWait([(By.ID, "audio-source"), (By.XPATH, '//*[contains(text(), "computer or network")]')]) == 1:
            self.driver.switch_to.parent_frame()
            return False

        src = self.driver.find_element(By.ID, "audio-source").get_attribute("src")
        # Your server here that handle audio
        data = {'type': 'recaptcha-audio', 'src': src}
        response = requests.post(f'{self.HOST}/resolve', json=data)
        result = response.json()['response']

        # Bad request response here
        if result is not None:
            self.reload_captcha()
            self.driver.switch_to.parent_frame()
            self.delay.custom(5)
            return self._solve()

        audio_elm = self.driver.find_element(By.ID, "audio-response")
        audio_elm.send_keys(result.lower())
        self.verify_captcha()
        self.driver.switch_to.parent_frame()
        self.delay.custom(2)

        if self.multiWait([self.multiple_correct_prompt, self.retry_prompt, self.recaptcha_response]) != 2:
            return self._solve()
        return True

    def solve(self):
        self.real_hook_frame()
        logger.debug("Challenge handling")
        response_id = self.multiWait([self.anti_checkbox, self.is_banner_visible, self.recaptcha_response, self.next_locator])
        if response_id == 0:
            response_id = self.multiWait([lambda: 1 == 2, self.is_banner_visible, self.recaptcha_response, self.next_locator])
        if response_id == 1:
            self.real_challenge_frame()
            self.driver.switch_to.frame(self.CHALLENGE_FRAME[1])
            audio_btn = self.find_element(By.ID, 'recaptcha-audio-button', (NoSuchElementException,))
            if audio_btn is not None and audio_btn.is_displayed():
                logger.debug("Switched to audio challenge")
                self.click_js(audio_btn)
                self.delay.one_3()
            self.driver.switch_to.parent_frame()
            return self._solve()
        else:
            response = True

        logger.debug(f"Response: {response}")
        return response
