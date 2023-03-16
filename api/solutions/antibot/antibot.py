import urllib.request
from collections import Counter
from typing import Union, Any

import requests

from ..common import path_to_base64, indexN, argmin, Selenium, By, EC


class AntiBotLinks(Selenium):

    def __init__(self, host, driver, wait, storage,
                 object_image_locator=(By.XPATH, '//*[@class="alert alert-warning text-center"]/img'),
                 input_image_locator=(By.XPATH, '//div[@class="antibotlinks"]/a/img')):
        super().__init__()
        self.HOST = host
        self.driver = driver
        self.wait = wait
        self.storage = storage
        self.object_image_locator = object_image_locator
        self.input_image_locator = input_image_locator

    def solve(self) -> Union[bool, list[Any]]:
        """Solve antibot_links patterns using machine learning model"""
        paths = []
        path_to_obj = f"{self.storage}/object.png"
        obj_ref = self.wait.until(EC.presence_of_element_located(self.object_image_locator)).get_attribute("src")
        urllib.request.urlretrieve(obj_ref, path_to_obj)
        paths.append(path_to_obj)

        # Download input image
        image_elm = self.wait.until(EC.presence_of_all_elements_located(self.input_image_locator))
        for i, x in enumerate(image_elm, 1):
            path_to_image = f"{self.storage}/img{i}.png"
            urllib.request.urlretrieve(x.get_attribute('src'), path_to_image)
            paths.append(path_to_image)

        # Solve images
        images = [path_to_base64(p, encoding='ascii') for p in paths]
        data = {'type': 'antibot', 'images': images}
        response = requests.post(f"{self.HOST}/resolve", json=data)
        res = response.json()['response']
        res = [(x[0], float(x[1])) for x in res]
        pred_obj, pred_inp = res[:3], res[3:]
        res_obj, score_obj = [x for x, y in pred_obj], [y for x, y in pred_obj]
        res_inp, score_inp = [x for x, y in pred_inp], [y for x, y in pred_inp]
        if len([x for x in sum([res_obj, res_inp], []) if x == 'nan']) > 2:
            return False

        sequence = [indexN(res_inp, x) for x in res_obj]
        if len([x for x in sequence if x != 'Not Found']) == 3:
            sequence[argmin(score_obj)] = 'Not Found'

        if max(Counter(sequence).values()) == 1:
            sequence[sequence.index('Not Found')] = 1 if 1 not in sequence else 2 if 2 not in sequence else 0
            return [image_elm[x] for x in sequence]
        else:
            return False
