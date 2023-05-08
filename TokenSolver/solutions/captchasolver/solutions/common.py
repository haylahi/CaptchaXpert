import base64
import logging
import random
import time
from typing import List, Union, Callable, Tuple, Dict, Optional, Any

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, ElementNotVisibleException, \
    ElementNotSelectableException, ElementClickInterceptedException, StaleElementReferenceException, NoSuchElementException, \
    NoSuchAttributeException, JavascriptException, InvalidArgumentException, InvalidSelectorException, InvalidSessionIdException, \
    NoSuchCookieException, NoSuchWindowException, NoSuchFrameException, NoAlertPresentException, UnexpectedAlertPresentException, \
    MoveTargetOutOfBoundsException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

logging.getLogger('selenium').setLevel(logging.ERROR)
logging.getLogger('urllib').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

__all__ = ['ActionChains', 'By', 'Options', 'EC', 'WebDriverWait', 'webdriver', 'Selenium', 'multiWait', 'Select',
           'safe_request', 'indexN', 'path_to_base64', 'multiWaitNsec', 'argmax', 'argmin',
           # **Exceptions**
           'TimeoutException', 'ElementNotInteractableException', 'ElementNotVisibleException', 'ElementNotSelectableException',
           'ElementClickInterceptedException', 'StaleElementReferenceException', 'NoSuchElementException',
           'NoSuchAttributeException', 'JavascriptException', 'InvalidArgumentException', 'InvalidSelectorException',
           'InvalidSessionIdException', 'NoSuchCookieException', 'NoSuchWindowException', 'NoSuchFrameException',
           'NoAlertPresentException', 'UnexpectedAlertPresentException', 'MoveTargetOutOfBoundsException',
           'WebDriverException'
           # **Exceptions**
           ]


def argmax(list_: list) -> int:
    """ Maximum value index in given list """
    return list_.index(max(list_))


def argmin(list_) -> int:
    """ Minimum value index in given list """
    return list_.index(min(list_))


def safe_request(src, headers=None, ignored_exceptions=(), on_error=None, image_path: str = None):
    try:
        response = requests.get(src, headers=headers)
    except ignored_exceptions:
        return on_error() if callable(on_error) else on_error
    else:
        if image_path is not None:
            with open(image_path, 'wb') as f:
                f.write(response.content)
        else:
            return response


def path_to_base64(path, encoding="bytes"):
    """ Read the given path to base64 string """

    with open(path, "rb") as image_file:
        b64 = base64.b64encode(image_file.read())
    if encoding == 'ascii':
        b64 = b64.decode('ascii')
    return b64


def indexN(list_: list, value, n=1, reverse_indices: bool = False) -> list or int or str:
    """
    Find x without raising ValueError
    :param reverse_indices: just reverse the index list
    :param n: number of indexes
    :param list_: list of items
    :param value: value to be found
    :return: indexes if n > 1 else indexes[0] if len(indexes) == 1 else 'Not Found'
    """

    if reverse_indices:
        list_ = list_[::-1]

    indexes = []
    i = 0
    for _ in range(n):
        try:
            i = list_.index(value, i)
            indexes.append(i)
            i += 1
        except ValueError:
            pass

    if reverse_indices:
        indexes = [len(list_) - 1 - y for y in indexes]

    return indexes if n > 1 else indexes[0] if len(indexes) == 1 else 'Not Found'


class Delay:

    def __init__(self):
        self.very_small_delay = self.one100_one1000
        self.small_delay = self.one10_one
        self.medium_delay = self.one_3
        self.long_delay = self.five_10
        self.very_long_delay = self.ten_15

    def _sleep(self, secs):  # noqa
        logger.debug(f"[Delay] Sleeping for {secs} seconds")
        time.sleep(secs)

    def one100_one1000(self):
        """Sleep Program for Random Between 0.001 - 0.01 seconds"""
        self._sleep(random.randint(1, 10) / 1000)

    def random_delay(self):
        """Sleep program for either very small delay or small delay or medium delay"""
        x = random.choice([1, 2, 3])
        self.very_small_delay() if x == 1 else self.small_delay() if x == 2 else self.medium_delay()

    def one10_one(self):
        """Sleep Program for Random Between 0.1 - 1 seconds"""
        self._sleep(random.randint(100, 1000) / 1000)

    def one_3(self):
        """Sleep Program for Random Between 1 - 3 seconds"""
        self._sleep(random.randint(1000, 3000) / 1000)

    def five_10(self):
        """Sleep Program for Random Between 5 - 10 seconds"""
        self._sleep(random.randint(5000, 1000) / 1000)

    def ten_15(self):
        """Sleep Program for Random Between 10 - 15 seconds"""
        self._sleep(random.randint(10000, 15000) / 1000)

    def btw(self, min, max):
        """Sleep Program for Random Between min - max seconds"""
        self._sleep(random.randint(min * 100, max * 100) / 100)

    def custom(self, secs):
        """Sleep program for time 't'"""
        self._sleep(secs)


class Selenium:
    """ Master class for all selenium scraping """

    __exceptions__ = (TimeoutException, ElementNotInteractableException, ElementNotVisibleException,
                      ElementNotSelectableException, ElementClickInterceptedException, StaleElementReferenceException,
                      NoSuchElementException,
                      NoSuchAttributeException, JavascriptException, InvalidArgumentException, InvalidSelectorException,
                      InvalidSessionIdException,
                      NoSuchCookieException, NoSuchWindowException, NoSuchFrameException, NoAlertPresentException,
                      UnexpectedAlertPresentException,
                      MoveTargetOutOfBoundsException, WebDriverException)

    def __init__(self, driver=None, wait=None, timeout=None):
        self.delay = Delay()
        self.driver = driver
        self.wait = wait
        self.timeout = timeout
        self.delay = Delay()

    def slow_type(self, element, content, value='default', click_human=False):
        """ Type slowly like human with random speed """

        logger.debug("===== Templates.selenium.slow_type =====")
        logger.debug(f"[Slow-Type] Sending {content} to web-element")
        if click_human:
            self.click_human(element)
        for x in content:
            if value == 'js':
                self.driver.execute_script(f'arguments[0].value += "{x}"', element)
            else:
                element.send_keys(x)
            self.delay.custom(random.uniform(0.1, 0.4))

    def find_element(self, by, value, ignore_exceptions: tuple or Exception = Exception):
        """ Find element given by and value, also return None in case of ignore_exception """
        try:
            return self.driver.find_element(by, value)
        except ignore_exceptions:
            logger.debug(f"[Find-Elements] Failed to find element at {by, value}")
            return None

    def find_elements(self, by, value, ignore_exceptions: tuple or Exception = Exception):
        """ Find elements given by and value, also return None in case of ignore_exception """
        try:
            return self.driver.find_elements(by, value)
        except ignore_exceptions:
            logger.debug(f"[Find-Elements] Failed to find elements at {by, value}")
            return None

    def click_action(self, elm=None):
        """ Click on given element or current location using ActionChains.click """

        logger.debug("[Click-Action] Performing click on element if possible else on current location")
        if elm is not None:
            ActionChains(self.driver).move_to_element(elm).click().perform()
        else:
            ActionChains(self.driver).click().perform()

    def click_js(self, arg, scroll_to_element_if_needed=False):
        """
        The method first checks if the arg parameter is a tuple, if it is then it uses that locator to find the element
        Then, it checks if scroll_to_element_if_needed is set to True, if it is then it calls scrollIntoViewIfNeeded method
        that scrolls the page to the element if needed
        Finally, it clicks on the element by calling the execute_script method of the WebDriver
        and passing in the element and the JavaScript click function
        """

        if isinstance(arg, tuple):
            logger.debug(f"[Click-JS] Finding element with {arg}")
            arg = self.driver.find_element(*arg)
        if scroll_to_element_if_needed:
            self.scrollIntoViewIfNeeded(arg)

        logger.debug(f"[Click-JS] Element clicked using javascript executor")
        self.driver.execute_script("arguments[0].click()", arg)

    def multiWaitNsec(self, locators, levels_of_persistency, refresh_url_every_n_sec=None):
        """ multiWait function should be persistent for given time """

        persistency = 0
        _prev_id = None
        ID = None
        while levels_of_persistency != persistency:
            ID = self.multiWait(locators, refresh_url_every_n_sec=refresh_url_every_n_sec)
            if ID != _prev_id and _prev_id is not None:
                logger.info(f"[MultiWaitNSec] Break: {locators[ID]}")
                persistency = 0
            _prev_id = ID
            logger.info(f"[MultiWaitNSec] Visible locator: {locators[ID]} && Persistency: {persistency + 1} second")
            time.sleep(1)
            persistency += 1
        return ID

    def multiWait(self, locators, output_type='id', refresh_url_every_n_sec=None):
        """ Same as multiWait with driver and timeout param filled """
        return multiWait(self.driver, locators, self.timeout, output_type, refresh_url_every_n_sec)

    def is_element_in_viewport(self, element):
        """ Is element visible on viewport """
        size = element.size
        location = element.location
        res = location['y'] >= 0 and location['y'] + size['height'] <= self.driver.execute_script("return window.innerHeight;")
        logger.debug("[Selenium] Element is not in viewport")
        return res

    def scrollIntoViewIfNeeded(self, element):
        """ Scroll to element if it is not visible on viewport """
        if not self.is_element_in_viewport(element):
            logger.debug('[Selenium] Element needed to be scrolled')
            self.scrollIntoView(element)
        logger.debug('[Selenium] Element does not need to be scrolled')

    def scrollIntoView(self, element):
        """ Scroll to element """
        logger.debug('[Selenium] Scrolled into element')
        self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center'});", element)

    def remove_element(self, element):
        """ Remove element from html document """
        logger.debug('[Selenium] Removed element from DOM!')
        self.driver.execute_script("arguments[0].remove();", element)

    def get(self, url):
        """ Go to the specified url """
        logger.info(f"[Selenium] Getting {url}")
        self.driver.get(url)

    def quit(self):
        """ Exit webdriver, also stop recording if needed """
        logger.info("[Selenium] Quitting driver")
        self.is_started = False
        self.is_running.clear()
        self.driver.quit()

    def refresh(self):
        """ Refresh webpage """
        logger.info("Refreshing web-page")
        self.driver.refresh()


def _multiWait(driver, locators, max_polls, output_type):
    """ multiWait in given timeout """

    logger.info('===== WebDriver-MultiWait =====')
    logger.debug(f'[MultiWait] Locators: {locators}')
    logger.debug(f"[MultiWait] Max-Polls: {max_polls}")
    wait = WebDriverWait(driver, 1)
    cp = 0
    while cp < max_polls:
        cp += 1
        for i, loc in enumerate(locators):
            if isinstance(loc, dict):
                func = loc.get('func')
                if func is not None:
                    fargs = loc.get('args')
                    if fargs is None:
                        fargs = ()
                    fkwds = loc.get('kwargs')
                    if fkwds is None:
                        fkwds = {}
                    if func(*fargs, **fkwds):
                        return i
                    time.sleep(1)
                else:
                    ec = loc.get('ec')
                    if ec is None:
                        ec = EC.presence_of_element_located(loc.get('locator'))
                    methods = loc.get('methods')
                    try:
                        element = wait.until(ec)
                        logger.debug(f"[MultiWait] Element found at {loc.get('locator')}")
                        if methods is not None:
                            logger.debug(f"[MultiWait] {loc.get('locator')} - Methods: {methods}")
                            if not all([eval(f"element.{m}()", {'element': element}) for m in methods]):
                                raise TimeoutException
                        logger.debug(f"[MultiWait] All methods exist on {loc.get('locator')}")
                        return i if output_type == 'id' else element
                    except TimeoutException:
                        pass
            else:
                if callable(loc):
                    if loc():
                        return i
                    time.sleep(1)
                else:
                    try:
                        element = wait.until(EC.presence_of_element_located(loc))
                        logger.debug(f'[MultiWait] Element found at {loc}')
                        return i if output_type == 'id' else element
                    except TimeoutException:
                        pass

        logger.debug(f"[MultiWait] Current-Polls: {cp}")


def multiWait(
        driver: webdriver,
        locators: List[Union[Callable, Tuple, Dict]],
        max_polls: int,
        output_type: str = 'id',
        refresh_url_every_n_sec: Optional[int] = None) -> Any:
    """
    Wait until any element found in the DOM.

    :param driver: a WebDriver instance
    :type locators: list[func, tuples] or list[dict[func, loc]]
    :param locators: a list of locators or locator with its method like is_displayed, click etc
    :param max_polls: max number of time check given locator
    :param output_type: 'id' to get locator id or 'element' to get the resulting element
    :param refresh_url_every_n_sec: refresh the url every n seconds, if provided
    :return: output as specified by the output parameter
    :raises: TimeoutException if none of the elements are present in the DOM
    """

    if refresh_url_every_n_sec is not None:
        iters = int(max_polls / refresh_url_every_n_sec)
        max_polls = refresh_url_every_n_sec

    resp = _multiWait(driver, locators, max_polls, output_type)
    if refresh_url_every_n_sec is not None:
        for iter in range(iters - 1):
            if resp is None:
                driver.refresh()
            else:
                return resp
        resp = _multiWait(driver, locators, max_polls, output_type)

    if resp is None:
        raise TimeoutException("None of the given element is present in the DOM!")
    return resp


def multiWaitNsec(driver, locators, _time, timeout, refresh_url_every_n_sec=None):
    """ MultiWait should be persistent for given time """
    ID = None
    for i in range(_time):
        ID = multiWait(driver, locators, timeout, refresh_url_every_n_sec=refresh_url_every_n_sec)
        logger.info(f"Visible locator: {locators[ID]} && Persistency: {i + 1} seconds")
        time.sleep(1)
    return ID
