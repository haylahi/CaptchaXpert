import os
import shutil

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait

from selenium.common.exceptions import (
    TimeoutException, ElementNotInteractableException, ElementNotVisibleException, \
    ElementNotSelectableException, ElementClickInterceptedException, StaleElementReferenceException, NoSuchElementException, \
    NoSuchAttributeException, JavascriptException, InvalidArgumentException, InvalidSelectorException, InvalidSessionIdException, \
    NoSuchCookieException, NoSuchWindowException, NoSuchFrameException, NoAlertPresentException, UnexpectedAlertPresentException, \
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


def init_proxy_server(options, proxy):
    if isinstance(proxy, str):
        options.add_argument(f"--proxy-server={proxy}")
    else:
        host = proxy['host']
        port = proxy['port']
        protocol = proxy.get('protocol') if proxy.get('protocol') is not None else 'http'
        username = proxy.get('username')
        password = proxy.get('password')
        plugin_dir = proxy.get('plugin_location') if proxy.get('plugin_location') is not None else 'extension'
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

        try:
            os.makedirs(plugin_dir)
        except FileExistsError:
            shutil.rmtree(plugin_dir)
            os.makedirs(plugin_dir)
        with open(f'{plugin_dir}/manifest.json', 'w') as f:
            f.write(manifest_json)
        with open(f'{plugin_dir}/background.js', 'w') as f:
            f.write(background_js)
        options.add_argument(f'--load-extension={os.path.abspath(plugin_dir)}')
        return plugin_dir


def create_driver(proxy=None, driver_executable_path=None, arguments=None, headless2=False):
    options = Options()
    if proxy is not None:
        plugin_dir = init_proxy_server(options, proxy)
    if arguments is not None:
        for arg in arguments:
            options.add_argument(arg)
    driver = uc.Chrome(driver_executable_path=driver_executable_path, options=options,
                       use_subprocess=True, suppress_welcome=True, )
    if proxy is not None:
        shutil.rmtree(plugin_dir)
    return driver
