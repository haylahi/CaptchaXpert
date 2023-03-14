import logging
import os
import random
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from multiprocessing.pool import ThreadPool
from ..common.delays import Delay
from ..common.functools import get_func_name
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
logger = logging.getLogger(__name__)

__all__ = ['ActionChains', 'By', 'Options', 'EC', 'WebDriverWait', 'webdriver', 'Selenium', 'multiWait', 'Select',
           'table_scrape', 'length_of_window_handles_become', 'length_of_window_handles_less_than',
           'length_of_window_handles_greater_than', 'multiWaitNsec',
           # **Exceptions**
           'TimeoutException', 'ElementNotInteractableException', 'ElementNotVisibleException', 'ElementNotSelectableException',
           'ElementClickInterceptedException', 'StaleElementReferenceException', 'NoSuchElementException',
           'NoSuchAttributeException', 'JavascriptException', 'InvalidArgumentException', 'InvalidSelectorException',
           'InvalidSessionIdException', 'NoSuchCookieException', 'NoSuchWindowException', 'NoSuchFrameException',
           'NoAlertPresentException', 'UnexpectedAlertPresentException', 'MoveTargetOutOfBoundsException',
           'WebDriverException'
           # **Exceptions**
           ]
clientX, clientY, scrollX, scrollY = 0, 0, 0, 0


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

    def __init__(
            self,
            webdriver_: str = "chrome",
            user_data_dir: str = None,
            incognito: bool = False,
            proxy_server: dict or str = None,
            headless1: bool = False,
            headless2: bool = False,
            load_full: bool = False,
            timeout: int = 30,
            zoom: Union[float, int] = None,
            stealth: bool = False,
            args: Tuple[str] = (),
            extensions: List[str] or Tuple[str] = (),
            use_tor_proxy: bool = False,
            options: Optional[Any] = None,
            user_agent: str = None,
            start: bool = False):
        """
        :param webdriver_: The webdriver to use for the class. Default is "chrome"
        :param user_data_dir: The path to the user data directory. Default is None
        :param incognito: A boolean indicating whether to start the browser in incognito mode. Default is False
        :param proxy_server: A string representing the proxy server to use. Default is None
        :param headless1: A boolean indicating whether to run the browser in headless mode. Default is False (Old method)
        :param headless2: A boolean indicating whether to run the browser in headless mode. Default is False
        :param load_full: A boolean indicating whether to load the full page or just the visible content. Default is False
        :param timeout: An integer representing the timeout for the browser in seconds. Default is 30
        :param zoom: A float or integer representing the zoom level for the browser. Default is None
        :param stealth: A boolean indicating whether to run the browser in stealth mode. Default is False
        :param args: A tuple of strings representing command line arguments to pass to the browser. Default is an empty tuple
        :param extensions: A tuple of strings representing the path to the browser extensions to be loaded. Default is an empty tuple
        :param use_tor_proxy: A boolean indicating whether to use a Tor proxy or not. Default is False
        :param options: An instance of a class that contains additional options for the browser. Default is None
        :param start: A boolean indicating whether to start the browser immediately after initialization. Default is False
        """

        self._webdriver = webdriver_
        self._user_agent = user_agent
        self._headless1 = headless1
        self._headless2 = headless2
        self._incognito = incognito
        self._user_data_dir = user_data_dir
        self._load_full = load_full
        self._use_tor_proxy = use_tor_proxy
        self._extensions = extensions
        self._args = args
        self._zoom = zoom
        self._proxy_server = proxy_server
        self._stealth = stealth
        self._options = None

        if options is None:
            self.__init_options__()
        else:
            self._options = options

        self.delay = Delay()
        self.driver = None
        self.wait = None
        self.timeout = timeout
        self.is_verbose = 'verbose' in ''.join(sys.argv)
        self.is_started = False
        self.is_rec_running = threading.Event()
        self.is_running = threading.Event()
        self._plugin_file = None
        try:
            from mytools.common.mouse import wind_mouse
            self.wind_mouse = wind_mouse
        except ImportError:
            pass

        self.start() if start else ''

    def __init_options__(self):
        """ Initialize Options class using given params """

        logger.debug("[Selenium.Options] Compiling options")
        self._options = Options()
        self._options.add_argument(f"--user-agent={self._user_agent}") if self._user_agent is not None else ''
        self._options.add_argument("--headless=new") if self._headless2 else ''
        if not self._headless2:
            self._options.add_argument("--headless") if self._headless1 else ''
        self._options.add_argument(
            f"--force-device-scale-factor={self._zoom} --high-dpi-support={self._zoom}") if self._zoom is not None else ''
        self._options.add_argument("--incognito") if self._incognito else ''
        [self._options.add_argument(arg) for arg in self._args]
        [self._options.add_extension(ext) for ext in self._extensions]
        self._options.page_load_strategy = "none" if not self._load_full else 'normal'
        if self._user_data_dir is not None:
            if isinstance(self._user_data_dir, int):
                self._user_data_dir = fr"C:\Users\HP\AppData\Local\Google\Chrome\User Data\Profile {self._user_data_dir}"
            self._options.add_argument(f"--user-data-dir={self._user_data_dir}")
        if self._webdriver == 'chrome':
            if self._headless1 or self._headless2:
                self._options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML'
                                           ', like Gecko) Chrome/68.0.3440.84 Safari/537.36')
            self._options.add_experimental_option("excludeSwitches", ["enable-automation"])
            self._options.add_experimental_option('useAutomationExtension', False)
            self._options.add_experimental_option("prefs", {"profile.default_content_setting_values.popups": 1, })
            self._options.add_argument("--disable-infobars")
            self._options.add_argument("--disable-notifications")
            self._options.add_argument('--no-sandbox')
            # self._options.add_argument('--disable-application-cache')
            self._options.add_argument('--disable-gpu')
            self._options.add_argument("--start-maximized")
            self._options.add_argument("--disable-dev-shm-usage")

        if self._use_tor_proxy:
            subprocess.run('TASKKILL /f /im "tor.exe"', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            subprocess.Popen(r'C:\Users\HP\OneDrive\Desktop\Tor Browser\Browser\TorBrowser\Tor\tor.exe')
            self._options.add_argument('--proxy-server=socks5://localhost:9050')

        # Adding proxy capabilities
        if self._proxy_server is not None:
            self.init_proxy_server()
        logger.debug("[Selenium.Options] Options compiled")

    def init_proxy_server(self):
        if isinstance(self._proxy_server, str):
            self._options.add_argument(f"--proxy-server={self._proxy_server}")
        else:
            host = self._proxy_server['host']
            port = self._proxy_server['port']
            protocol = self._proxy_server.get('protocol') if self._proxy_server.get('protocol') is not None else 'http'
            username = self._proxy_server.get('username')
            password = self._proxy_server.get('password')
            plugin_file = self._proxy_server.get('plugin_location') if self._proxy_server.get(
                'plugin_location') is not None else 'proxy_auth_plugin.zip'
            if username is None:
                bg_js_p1 = """
                authCredentials: {
                        password: "%s"
                    }
                    """ % password
            elif password is None:
                bg_js_p1 = """
                    authCredentials: {
                            username: "%s",
                        }
                        """ % username
            else:
                bg_js_p1 = """
                        authCredentials: {
                                username: "%s",
                                password: "%s"
                            }
                            """ % (username, password)

            manifest_json = """
            {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Chrome Proxy",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "<all_urls>",
                    "webRequest",
                    "webRequestBlocking"
                ],
                "background": {
                    "scripts": ["background.js"]
                },
                "minimum_chrome_version":"22.0.0"
            }
            """

            background_js = """
            var config = {
                    mode: "fixed_servers",
                    rules: {
                    singleProxy: {
                        scheme: "%s",
                        host: "%s",
                        port: parseInt(%s)
                    },
                    bypassList: ["localhost"]
                    }
                };

            chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

            function callbackFn(details) {
                return {
                    %s
                };
            }

            chrome.webRequest.onAuthRequired.addListener(
                        callbackFn,
                        {urls: ["<all_urls>"]},
                        ['blocking']
            );
            """ % (protocol, host, port, bg_js_p1)

            with zipfile.ZipFile(plugin_file, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)

            self._options.add_extension(plugin_file)
            self._plugin_file = plugin_file

    def reset_chain(self):
        """ Reset clientX, clientY, scrollX, scrollY to 0 """
        global clientX, clientY, scrollX, scrollY
        clientX, clientY, scrollX, scrollY = 0, 0, 0, 0

    def start(self):
        """ Start webdriver (uc, webdriver, seleniumBase) """

        logger.debug(f"[Selenium.start] Starting {self._webdriver}.driver")
        if self._webdriver == "uc":
            import undetected_chromedriver as uc
            from webdriver_manager.chrome import ChromeDriverManager
            self.driver = uc.Chrome(driver_executable_path=ChromeDriverManager().install(), advanced_elements=True,
                                    options=self._options, use_subprocess=True, suppress_welcome=True)
            self.driver.maximize_window()
        elif self._webdriver.lower() == "chrome":
            from webdriver_manager.chrome import ChromeDriverManager
            self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=self._options)
        elif self._webdriver.lower() == "firefox":
            from webdriver_manager.firefox import GeckoDriverManager
            self.driver = webdriver.Chrome(GeckoDriverManager().install(), options=self._options)
        elif self._webdriver.lower() == 'seleniumbase':
            from seleniumbase import Driver
            self.driver = Driver(headless2=self._headless, uc=True,
                                 user_data_dir=self._user_data_dir,
                                 page_load_strategy=self._options.page_load_strategy,
                                 )
            self.driver.maximize_window()
        else:
            raise NotImplementedError(f"{self._webdriver} is not implemented yet!")
        if self._stealth:
            from selenium_stealth import stealth  # noqa
            stealth(self.driver, platform='Win32', fix_hairline=True)

        self.wait = WebDriverWait(self.driver, self.timeout)
        self.is_started = True
        self.is_running.set()
        if self._plugin_file is not None:
            os.remove(self._plugin_file)
        logger.debug(f"[Selenium.start] {self._webdriver}.driver is ready to use!")

    def move_human(self, element=None, xoffset=0, yoffset=0, fluctuationX=5, fluctuationY=5):
        """
        Human like mouse movement performed and then clicked on element
        -> xoffset and element cannot be None
        :param element: input element (Optional)
        :param xoffset: move x offset (Optional)
        :param yoffset: move y offset (Optional)
        """
        global clientX, clientY

        if self.is_verbose:
            print("Simulating human movement")
        if element is not None:
            # elx, ely, esx, esy = element.location['x'], element.location['y'], element.size['width'], element.size['height']
            # xoffset, yoffset = int(elx + (esx / 2)), int(ely + (esy / 2)) - scrollY  # determining mid point
            rect = self.driver.execute_script("return arguments[0].getBoundingClientRect()", element)
            xoffset = rect['x'] + rect['width'] / 2
            yoffset = rect['y'] + rect['height'] / 2

        # Fluctuation
        xoffset = xoffset + random.randint(0, fluctuationX) if random.randint(0, 1) == 0 else xoffset - random.randint(0,
                                                                                                                       fluctuationX)
        yoffset = yoffset + random.randint(0, fluctuationY) if random.randint(0, 1) == 0 else yoffset - random.randint(0,
                                                                                                                       fluctuationY)

        # Points of curve
        points = self.wind_mouse(clientX, clientY, xoffset, yoffset, W_0=7, M_0=8)
        for i in range(len(points) - 2):
            try:
                px, py = (points[i + 1][0] - points[i][0]), (points[i + 1][1] - points[i][1])
                ActionChains(self.driver, duration=0).move_by_offset(xoffset=px, yoffset=py).perform()
            except MoveTargetOutOfBoundsException:
                pass
        clientX, clientY = xoffset, yoffset

    def click_human(self, element=None, xoffset=None, yoffset=None, fluctuationX=5, fluctuationY=5,
                    action_click=True, delay=0.1):
        """
        Human like mouse movement performed and then clicked on element
        -> xoffset and element cannot be None
        :param element: input element (Optional)
        :param xoffset: move x offset (Optional)
        :param yoffset: move y offset (Optional)
        :param action_click: Use action chains to click on element
        :param delay: Sleep in seconds after clicking on elment
        :return: None
        """

        self.move_human(element, xoffset, yoffset, fluctuationX, fluctuationY)
        if action_click:
            self.click_action()
        else:
            assert element is not None, "How can you click_js without knowing element?"
            self.click_js(element)
        if self.is_verbose:
            print(f"Sleeping for {delay}s")
        time.sleep(delay)

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
        global scrollX, scrollY
        logger.debug('[Selenium] Scrolled into element')
        self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center'});", element)
        for i in range(4):
            time.sleep(1)
            _scrollX = self.driver.execute_script("return window.scrollX")
            _scrollY = self.driver.execute_script("return window.scrollY")
            if (_scrollX != scrollX) or (_scrollY != scrollY):
                scrollX, scrollY = _scrollX, _scrollY
                break
        ActionChains(self.driver).move_by_offset(-scrollX, -scrollY)

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
        self.is_rec_running.clear()
        self.driver.quit()

    def refresh(self):
        """ Refresh webpage """
        logger.info("Refreshing web-page")
        self.driver.refresh()

    def debug_mouse(self):
        """ Debug mouse actions by drawing red circle on current mouse location """

        logger.info('[DebugMouse] Adding white color over mouse location to debug mouse')
        script = \
            """
            document.addEventListener('mousemove', function(event) {
            var x = event.clientX + window.scrollX;
            var y = event.clientY + window.scrollY;
            console.log("Mouse:", x, y)

            var dot = document.createElement('div');
            dot.style.position = 'absolute';
            dot.style.left = x + 'px';
            dot.style.top = y + 'px';
            dot.style.width = '3px';
            dot.style.height = '3px';
            dot.style.backgroundColor = 'red';

            document.body.appendChild(dot);
            });
            """
        self.driver.execute_script(script)

    def scrollBy(self, x, y, element="body", method="incremental", incremental_stepX=5, incremental_stepY=5, sleep=0):
        """
        Scroll webpage or webelement by given coordinate::

        :param x: x coordinate
        :param y: y coordinate
        :param element: body or webelement
        :param method: direct or incremental
        :param incremental_stepX: increase step X
        :param incremental_stepY: increase step Y
        :param sleep: sleep on each step

        :return: None
        """

        logger.debug(f"[ScrollBy] Method: {method}, (x, y): {x, y}, IncrementalStepX-Y: {incremental_stepX, incremental_stepY}, "
                     f"Sleep on each step: {sleep}")
        if method == "direct":
            if element == "body":
                self.driver.execute_script(f"window.scrollBy({x}, {y});")
            else:
                self.driver.execute_script(f"arguments[0].scrollBy({x}, {y});", element)
        elif method == "incremental":
            is_x, is_y = False, False
            _x, _y = 0, 0
            if element == "body":
                while True:
                    if _x <= x:
                        self.driver.execute_script(f"window.scrollBy({incremental_stepX}, 0);")
                        _x += incremental_stepX
                    else:
                        is_x = True
                    if _y <= y:
                        self.driver.execute_script(f"window.scrollBy(0, {incremental_stepY});")
                        _y += incremental_stepY
                    else:
                        is_y = True
                    time.sleep(sleep)

                    if is_x and is_y:
                        break
            else:
                while True:
                    if _x <= x:
                        self.driver.execute_script(f"arguments[0].scrollBy({incremental_stepX}, 0);", element)
                        _x += incremental_stepX
                    else:
                        is_x = True
                    if _y <= y:
                        self.driver.execute_script(f"arguments[0].scrollBy(0, {incremental_stepY});", element)
                        _y += incremental_stepY
                    else:
                        is_y = True
                    time.sleep(sleep)

                    if is_x and is_y:
                        break

        else:
            raise WebDriverException("No such method detected!")

    def scrollTo(self, x, y, element="body", method="incremental", incremental_stepX=5, incremental_stepY=5, sleep=0):
        """
        Scroll webpage or webelement to given coordinate::

        :param x: x coordinate
        :param y: y coordinate
        :param element: body or webelement
        :param method: direct or incremental
        :param incremental_stepX: increase step X
        :param incremental_stepY: increase step Y
        :param sleep: sleep on each step

        :return: None
        """

        logger.debug(f"[ScrollTo] Method: {method}, (x, y): {x, y}, IncrementalStepX-Y: {incremental_stepX, incremental_stepY}, "
                     f"Sleep on each step: {sleep}")
        if method == "direct":
            if element == "body":
                self.driver.execute_script(f"window.scrollTo({x}, {y});")
            else:
                self.driver.execute_script(f"arguments[0].scrollTo({x}, {y});", element)
        elif method == "incremental":
            is_x, is_y = False, False
            _x, _y = 0, 0
            if element == "body":
                while True:
                    if _x <= x:
                        self.driver.execute_script(f"window.scrollTo({incremental_stepX}, 0);")
                        _x += incremental_stepX
                    else:
                        is_x = True
                    if _y <= y:
                        self.driver.execute_script(f"window.scrollTo(0, {incremental_stepY});")
                        _y += incremental_stepY
                    else:
                        is_y = True
                    time.sleep(sleep)

                    if is_x and is_y:
                        break
            else:
                while True:
                    if _x <= x:
                        self.driver.execute_script(f"arguments[0].scrollTo({incremental_stepX}, 0);", element)
                        _x += incremental_stepX
                    else:
                        is_x = True
                    if _y <= y:
                        self.driver.execute_script(f"arguments[0].scrollTo(0, {incremental_stepY});", element)
                        _y += incremental_stepY
                    else:
                        is_y = True
                    time.sleep(sleep)

                    if is_x and is_y:
                        break

        else:
            raise WebDriverException("No such method detected!")

    def start_recording(self, output_path, _poll_frequency=0.1, fps=1):
        """ Start recording webdriver """

        self.is_rec_running.set()
        ThreadPool(processes=1).apply_async(record, args=(self.driver, output_path, self.is_rec_running, _poll_frequency, fps))


class length_of_window_handles_become(object):
    """ Wait until length of window handles changes """

    def __init__(self, window_handles_length):
        self.expected_count = window_handles_length

    def __call__(self, driver):
        logger.debug(f'Length of window_handles changes to {len(driver.window_handles)}')
        return len(driver.window_handles) == self.expected_count


class length_of_window_handles_greater_than(object):
    """ Wait until length of window handles changes """

    def __init__(self, window_handles_length):
        self.expected_count = window_handles_length

    def __call__(self, driver):
        logger.debug(f'Length of window_handles changes to {len(driver.window_handles)}')
        return len(driver.window_handles) > self.expected_count


class length_of_window_handles_less_than(object):
    """ Wait until length of window handles changes """

    def __init__(self, window_handles_length):
        self.expected_count = window_handles_length

    def __call__(self, driver):
        logger.debug(f'Length of window_handles changes to {len(driver.window_handles)}')
        return len(driver.window_handles) < self.expected_count


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
                        logger.debug(f'[MultiWait] func: {get_func_name(loc)} returned true')
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
                        logger.debug(f'[MultiWait] func: {get_func_name(loc)} returned true')
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


def slow_type(element, content):
    """ Type slowly with custom speed """

    logger.debug("===== Templates.selenium.slow_type =====")
    logger.debug(f"[Slow-Type] Sending {content} to web-element")
    for x in content:
        element.send_keys(x)
        Delay().btw(0.2, 0.4)


def table_scrape(table, rows=0, columns=0, header=False, get_links=False, reverse=False, get_element=False):
    """
    Scrape given table element
        -> get_links or element cannot be true at a time
    :param table: webdriver table element
    :param rows: no of rows to scrape
    :param columns: no of columns to scrape
    :param header: include header or not
    :param get_links: get associated links or not
    :param reverse: reverse the table or not
    :param get_element: get associated element or not
    :return: dict of thead and tbody containing list of table elements text or list of tuple of table elment and text
    """

    data = {
        "thead": [],
        "tbody": [],
    }

    # Table head
    if header:
        thead = table.find_element(By.TAG_NAME, "thead")
        trH = thead.find_elements(By.TAG_NAME, "tr")
        trH.reverse() if reverse else ''
        for tr in range(len(trH)):
            row = []
            thH = trH[tr].find_elements(By.TAG_NAME, "th")
            thH.reverse() if reverse else ''
            if columns == 0: columns = len(thH)
            for r in range(columns):
                if get_links:
                    links = []
                    for x in thH[r].find_elements(By.TAG_NAME, "a"):
                        if 'http' in x.get_attribute("href"):
                            links.append(x.get_attribute("href"))
                        elif 'http' in x.get_attribute("src"):
                            links.append(x.get_attribute("src"))
                    row.append((thH[r].text, links))
                elif get_element:
                    row.append((thH[r], thH[r].text))
                else:
                    row.append(thH[r].text)
            data["thead"].append(row)

    # Table Body
    tbody = table.find_element(By.TAG_NAME, "tbody")
    trB = tbody.find_elements(By.TAG_NAME, "tr")
    trB.reverse() if reverse else ''
    if rows == 0: rows = len(trB)
    for tr in range(rows):
        row = []
        tdB = trB[tr].find_elements(By.TAG_NAME, "td")
        tdB.reverse() if reverse else ''
        if columns == 0: columns = len(tdB)
        for r in range(columns):
            if get_links:
                links = []
                for x in tdB[r].find_elements(By.TAG_NAME, "a"):
                    if 'http' in x.get_attribute("href"):
                        links.append(x.get_attribute("href"))
                    elif 'http' in x.get_attribute("src"):
                        links.append(x.get_attribute("src"))
                row.append((tdB[r].text, links))
            elif get_element:
                row.append((tdB[r], tdB[r].text))
            else:
                row.append(tdB[r].text)
        data["tbody"].append(row)
    return data


def record(driver, output_path, is_rec_running, _poll_frequency=0.1, fps=30.0):
    """ Record webdriver actions by opening it in thread """

    logger.info('Web-Browser recording started')
    _temp_cache_path = os.path.join(os.path.dirname(__file__), '_temp_cache')
    shutil.rmtree(_temp_cache_path, ignore_errors=True)
    os.mkdir(_temp_cache_path)

    # Send *args to our merger server
    data = {'pid': os.getpid(), 'input_dir': _temp_cache_path, 'output_path': output_path, 'fps': fps}
    requests.get("http://127.0.0.1:5000/merger", json=data)

    # Saving screenshots
    i = 0
    while is_rec_running.is_set():
        driver.save_screenshot(f"{_temp_cache_path}/_ss{i}.png")
        i += 1
        time.sleep(_poll_frequency)

    logger.info('Web-Browser recording finished')
