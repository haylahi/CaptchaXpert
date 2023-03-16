import argparse
import time
from collections import Counter

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

try:
    from api import CaptchaSolver  # This is in our deployment package # noqa
except ImportError:
    from CaptchaXpert import CaptchaSolver  # This is in our local package
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()],
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', )

logging.getLogger('selenium').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)

analyst = []
HCAPTCHA_TEST_URL = "https://nopecha.com/demo/hcaptcha"
RECAPTCHA_TEST_URL = "https://nopecha.com/demo/recaptcha"

parser = argparse.ArgumentParser()
parser.add_argument('-h1', '--headless1', action="store_true", help="Run selenium in headless chrome")
parser.add_argument('-h2', '--headless2', action="store_true", help="Run selenium in headless chrome version 2")
parser.add_argument('-n', '--no_of_tests', default=10, type=int, help="No of tests to perform")
parser.add_argument('-t', '--test', default=1, type=int, help="choose test:\n"
                                                              "1: recaptcha_v2\n"
                                                              "2: recaptcha_v2 on custom frame\n"
                                                              "3: hcaptcha\n"
                                                              "4: hcaptcha on custom frame")
pargs = parser.parse_args()


def init_driver():
    options = Options()
    options.page_load_strategy = 'none'
    if pargs.headless1:
        options.add_argument('--headless')
    elif pargs.headless2:
        options.add_argument('--headless=new')
    _driver = uc.Chrome(driver_executable_path=ChromeDriverManager().install(), options=options)
    _driver.maximize_window()
    return _driver


def preprocess(func):
    def wrapper(*args, **kwargs):
        try:
            return n_tests(func, *args, **kwargs)
        finally:
            logger.info(f"====== Results ======\n"
                        f"Responses: {analyst}\n"
                        f"Counter: {Counter([x[0] for x in analyst])}\n"
                        f"Time: {sum(x[1] for x in analyst)}")
            driver.quit()

    return wrapper


def n_tests(func, tests=pargs.no_of_tests, *args, **kwargs):
    results = []
    for _ in range(tests):
        s = time.time()
        result = func(*args, **kwargs)
        e = time.time()
        analyst.append((result, round(e - s, 3)))
        results.append(result)
        logger.info(f"Response: {result} in {e - s}")
    return results


@preprocess
def run_recaptcha_v2_test():
    solver.setCaptchaTypeAsRecaptchaV2()
    driver.get(RECAPTCHA_TEST_URL)
    return solver.solve()


@preprocess
def run_recaptcha_test_on_second_captcha():
    solver.setCaptchaTypeAsRecaptchaV2()
    driver.get(RECAPTCHA_TEST_URL)
    hook_frame = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, '//div[@data-sitekey="6LfLenAiAAAAACS1GtMiomQSQWjj2L9D9tDm0D4z"]/div/div/iframe')
        )
    )
    challenge_frame = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[4]/div[4]/iframe')
        )
    )
    solver._HOOK_FRAME = hook_frame
    solver._CHALLENGE_FRAME = challenge_frame
    solver.response_locator = (By.XPATH, '//*[@id="g-recaptcha-response-1"]')
    return solver.solve()


@preprocess
def run_hcaptcha_test():
    solver.setCaptchaTypeAsHcaptcha()
    driver.get(HCAPTCHA_TEST_URL)
    return solver.solve()


@preprocess
def run_hcaptcha_test_on_second_captcha():
    solver.setCaptchaTypeAsHcaptcha()
    driver.get(HCAPTCHA_TEST_URL)
    hook_frame = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, '//div[@data-sitekey="2c823188-d286-4a5e-9d7e-c0c9290393f6"]/iframe')
        )
    )
    challenge_frame = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[3]/div[1]/iframe')
        )
    )
    solver._HOOK_FRAME = hook_frame
    solver._CHALLENGE_FRAME = challenge_frame
    return solver.solve()


if __name__ == '__main__':
    driver = init_driver()
    solver = CaptchaSolver(driver, destroy_storage=True, timeout=100, image_getting_method="screenshot")
    logger.info('Success initialized!')

    if pargs.test == 1:
        run_recaptcha_v2_test()
    elif pargs.test == 2:
        run_recaptcha_test_on_second_captcha()
    elif pargs.test == 3:
        run_hcaptcha_test()
    elif pargs.test == 4:
        run_hcaptcha_test_on_second_captcha()
    else:
        raise TypeError('This type of test is not yet defined!')
