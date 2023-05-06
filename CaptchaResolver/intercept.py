import json
import logging
import os
import time
import uuid
from datetime import datetime

import cv2
import numpy as np
import yaml

from solutions.tools.pre_processing import pimage, pconversion, plist
from solutions.antibot.inference import predict as antibot_predictor
from solutions.hcaptcha.inference import predict as hcaptcha_predictor
from solutions.recaptcha.inference import predict as recaptcha_predictor
from solutions.viefaucet.inference import predict as vie_predictor
logger = logging.getLogger(__name__)
with open('track.yaml', 'r') as tracker:
    objects_to_track = yaml.safe_load(tracker)


def intercept(data, debugger=True):
    """
    Perform detection
    :param data::
        type: hcaptcha or antibot or viefaucet or recaptcha
        prompt: if hcaptcha or recaptcha(send label)
        images: base64 images
    :param debugger: true if you want to save unsolved images for later processing else false
    :return: predictions
    """

    start_time = time.time()
    results = {}
    if data['type'] == 'vie_antibot':
        images = [pconversion.base64_to_cv2(b64_str) for b64_str in data['images']]
        images = [cv2.resize(img, (40, 40)).astype(np.float32) for img in images]
        images = [cv2.cvtColor(img, cv2.COLOR_GRAY2RGB) for img in images]
        images = [np.reshape(img, (1, 40, 40, 3)) for img in images]
        response = [vie_predictor(img, scores=True)[0] for img in images]
        results['response'] = [(x[0], str(x[1])) for x in response]
    elif data['type'] == 'antibot':
        images = [pconversion.base64_to_cv2(b64_str) for b64_str in data['images']]
        # Initialize images
        images = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) for img in images]
        images = [cv2.threshold(img, 125, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1] for img in images]
        images = [cv2.morphologyEx(img, cv2.MORPH_OPEN, np.ones((2, 2))) for img in images]
        obj_img, input_imgs = images[0], images[1:]

        # Split object image
        # Iterate through central y line, check white pixels difference and get top 2 differences as separators
        y = int(obj_img.shape[0] / 2)
        loc, pixels = [(y, x) for x in range(obj_img.shape[1])], [obj_img[y, x] for x in range(obj_img.shape[1])]
        white_indexes = [i for i, x in enumerate(pixels) if x == 255]
        # Consecutive difference
        dev_white = [0] + [white_indexes[w] - white_indexes[w - 1] for w in range(1, len(white_indexes))]
        # Max difference args
        x_max1, x_max2 = sorted(plist.argmaxN(np.array(dev_white), 2))
        # Max distance
        w1, w2 = int(dev_white[x_max1] / 2), int(dev_white[x_max2] / 2)
        # Starting points
        p1x, p2x = loc[white_indexes[x_max1 - 1]][1], loc[white_indexes[x_max2 - 1]][1]

        obj_imgs = ['obj1', 'obj2', 'obj3']
        obj_imgs[0] = obj_img[:, :p1x + w1]
        obj_imgs[1] = obj_img[:, p1x + w1:p2x + w2]
        obj_imgs[2] = obj_img[:, p2x + w2:]
        obj_imgs = pimage.remove_borders(obj_imgs)

        # Remove comma if possible
        obj_imgs = [pimage.findContours(img, 10) for img in obj_imgs]
        input_imgs = [pimage.findContours(img, 10) for img in input_imgs]
        obj_imgs = pimage.remove_borders(obj_imgs)
        input_imgs = pimage.remove_borders(input_imgs)

        images = sum([obj_imgs, input_imgs], [])
        images = [cv2.resize(img, (40, 40)).astype(np.float32) for img in images]
        images = [cv2.cvtColor(img, cv2.COLOR_GRAY2RGB) for img in images]
        images = [np.reshape(img, (1, 40, 40, 3)) for img in images]
        response = [antibot_predictor(img, scores=True)[0] for img in images]
        results['response'] = [(x[0], str(x[1])) for x in response]
    elif data['type'] == 'hcaptcha':
        imgs = [pconversion.base64_to_pil(img) for img in data['images']]
        results['response'] = hcaptcha_predictor(data['prompt'], imgs)
    elif data['type'] == 'recaptcha':
        if data.get('images') is not None:
            imgs = [cv2.cvtColor(pconversion.base64_to_cv2(img), cv2.COLOR_RGBA2BGR) for img in data['images']]
        else:
            imgs = cv2.cvtColor(pconversion.base64_to_cv2(data['image']), cv2.COLOR_RGBA2BGR)

        results['response'] = recaptcha_predictor(imgs, data['label'], data['grid'])
    else:
        results['response'] = 'InvalidCaptchaType'

    if debugger:
        if not results['response'] or data.get('label') in objects_to_track['Objects']:
            storage_path = os.path.join(os.path.dirname(__file__), "debugger", "json")
            os.makedirs(storage_path, exist_ok=True)
            data['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if data['type'] == 'recaptcha':
                json_path = os.path.join(storage_path, f"{data['type']}-{data['label']}-{uuid.uuid4()}.json")
            else:
                json_path = os.path.join(storage_path, f"{data['type']}-{uuid.uuid4()}.json")
            with open(json_path, 'w') as file:
                json.dump(data, file)
            logger.info(f"Data is saved in {json_path}")

    end_time = time.time()
    logger.info(f"Time-Consumption: {round(end_time - start_time, 2)} | Response: {results}")
    return results
