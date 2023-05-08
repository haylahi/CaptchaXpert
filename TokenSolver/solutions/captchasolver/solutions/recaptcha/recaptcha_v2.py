import logging
import random

import requests

from .common import *

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [RecaptchaV2Challenger] - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class RecaptchaV2(RecaptchaUtils):
    def _solve(self) -> bool:
        """Use ml models to classify image and solve recaptcha gracefully"""

        # Enter frame
        logger.debug("Switching to challenge frame")
        self.driver.switch_to.frame(self.CHALLENGE_FRAME)
        # Label __init__
        label = self.driver.find_element(By.TAG_NAME, 'strong').text
        logger.debug(f"Label found - {label}")

        # __init__ image | use either screenshot method or src method
        image_wrappers = {}
        for i in range(len(self.driver.find_elements(By.XPATH, '//div[@class="rc-imageselect-checkbox"]'))):
            image_wrappers[f'wrapper-{i}'] = {
                'xpath': f'//td[@tabindex="{i + 4}"]/div/div/img',
                'element': self.driver.find_element(By.XPATH, f'//td[@tabindex="{i + 4}"]/div/div/img'),
                'marked': False
            }

        image_element = self.find_element(By.XPATH, '//img')
        logger.debug("Image element found")
        img = self.get_image_as_base64(image_element, callback=self.retry_challenge)

        if len(image_wrappers) == 9:
            data = {'type': 'recaptcha', 'image': img, 'grid': '3x3', 'label': label}
            logger.debug("Resolving images...")
            response = requests.post(f"{self.HOST}/resolve", json=data)
            old_srcs = self.mark_images(response, image_wrappers, self.retry_challenge)
            if isinstance(old_srcs, bool):
                return True

            # Check if new tiles appear, solve them otherwise verify captcha
            # We generally use 5 iters to check if new tiles come, if new tiles come in the sixth time, the solver
            # just retry challenge
            script = 'return document.getElementsByClassName("rc-imageselect-tileselected").length === 0'
            logger.debug("Checking for new tiles")
            if self.driver.execute_script(script):
                new_tiles_limit = 10
                for t in range(new_tiles_limit):
                    self.wait_till_new_images([v['xpath'] for k, v in image_wrappers.items() if v['marked']], old_srcs)
                    self.delay.custom(2)    # explicit wait to ensure new images loaded
                    image_wrappers = {
                        k: {'xpath': v['xpath'], 'element': self.driver.find_element(By.XPATH, v['xpath']),
                            'marked': False} for k, v in image_wrappers.items() if v['marked']
                    }
                    imgs = []
                    for k, v in image_wrappers.items():
                        img = self.get_image_as_base64(v['element'], self.retry_challenge)
                        imgs.append(img)

                    data = {'type': 'recaptcha', 'images': imgs, 'grid': '1x1', 'label': label}
                    logger.debug("Resolving images...")
                    response = requests.post(f"{self.HOST}/resolve", json=data)
                    old_srcs = self.mark_new_images(response, image_wrappers)
                    if isinstance(old_srcs, bool):
                        break

                    # If limit reached retry challenge
                    if t == new_tiles_limit - 1:
                        logger.debug("End tile limit reached!")
                        return self.retry_challenge()

            # Click verify button
            logger.debug("All tiles handled")
            self.verify_captcha()

            # Exit frame
            logger.debug("Switching to parent frame")
            self.driver.switch_to.parent_frame()

            # Process response: on_error -> retry | on_success -> exit
            logger.debug("Checking challenge response")
            if self.multiWait([self.is_retry_prompt, self.recaptcha_response, self.next_locator]) == 0:
                logger.debug("Challenge continue")
                return self._solve()

            logger.debug("!!! Challenge successfully passed !!!")
            return True

        elif len(image_wrappers) == 16:
            data = {'type': 'recaptcha', 'image': img, 'grid': '4x4', 'label': label}
            logger.debug("Resolving images...")
            response = requests.post(f"{self.HOST}/resolve", json=data)
            res = response.json()['response']
            if not res or True not in res:
                logger.debug("Bad response.")
                return self.retry_challenge()

            # Marking images
            mapped_res = list(zip(range(16), res))
            random.shuffle(mapped_res)
            for i, x in mapped_res:
                if x:
                    self.click_js(image_wrappers[f'wrapper-{i}']['element'])
                    logger.debug(f"Marked {i}th image")
                    self.delay.btw(0.1, 0.3)

            # Click verify button
            verify_btn = self.driver.find_element(By.ID, 'recaptcha-verify-button')
            verify_btn_text = verify_btn.text
            if verify_btn == 'SKIP':
                self.reload_captcha()
            else:
                self.verify_captcha()

            # Exit frame
            self.driver.switch_to.parent_frame()
            logger.debug("Switched to parent frame")

            if verify_btn_text == 'NEXT' or verify_btn_text == 'SKIP':
                logger.debug("Challenge continue")
                self.delay.custom(3)  # small delay preventing detection
                return self._solve()
            else:
                logger.debug("Checking challenge response")
                if self.multiWait([self.is_retry_prompt, self.recaptcha_response, self.next_locator]) == 0:
                    logger.debug("Challenge continue")
                    return self._solve()

                logger.debug("!!! Challenge successfully passed !!!")
                return True

    def solve(self):
        self.real_hook_frame()
        logger.debug("Challenge handling")
        response_id = self.multiWait([self.anti_checkbox, self.is_banner_visible, self.recaptcha_response, self.next_locator])
        if response_id == 0:
            response_id = self.multiWait([lambda: 1 == 2, self.is_banner_visible, self.recaptcha_response, self.next_locator])
        if response_id == 1:
            self.real_challenge_frame()
            self.driver.switch_to.frame(self.CHALLENGE_FRAME)
            image_btn = self.find_element(By.ID, 'recaptcha-image-button', (NoSuchElementException,))
            if image_btn is not None and image_btn.is_displayed():
                logger.debug("Switched to vision challenge")
                self.click_js(image_btn)
                self.delay.one_3()
            self.driver.switch_to.parent_frame()
            response = self._solve()
        else:
            response = True

        logger.debug(f"Response: {response}")
        return response
