import re

import requests

from .common import *


class RecaptchaV3(RecaptchaUtils):
    raise NotImplementedError("Cannot solve this for now")

    def __init__(self):
        pass

    def solve(self):
        ANCHOR_URL = self.HOOK_FRAME.get_attribute('src')
        url_base = 'https://www.google.com/recaptcha/'
        post_data = "v={}&reason=q&c={}&k={}&co={}"

        client = requests.Session()

        client.headers.update({
            'content-type': 'application/x-www-form-urlencoded'
        })

        matches = re.findall('([api2|enterprise]+)\/anchor\?(.*)', ANCHOR_URL)[0]
        url_base += matches[0] + '/'
        params = matches[1]

        res = client.get(url_base + 'anchor', params=params)
        token = re.findall(r'"recaptcha-token" value="(.*?)"', res.text)[0]

        params = dict(pair.split('=') for pair in params.split('&'))
        post_data = post_data.format(params["v"], token, params["k"], params["co"])

        res = client.post(url_base + 'reload', params=f'k={params["k"]}', data=post_data)

        answer = re.findall(r'"rresp","(.*?)"', res.text)[0]
        token_element = self.driver.find_element(By.XPATH, '//textarea[contains(@id, "g-recaptcha-response")]')
        self.driver.execute_script(f'arguments[0].innerHTML = "{answer}";', token_element)
        return True

