import json
import logging
import os
import time
import uuid
from datetime import datetime

import cv2
import yaml

from solutions.antibot.inference import predict as antibot_predictor
from solutions.hcaptcha.inference import predict as hcaptcha_predictor
from solutions.recaptcha.inference import predict as recaptcha_predictor
from solutions.tools.pre_processing import pconversion

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
    if data['type'] == 'antibot':
        images = [pconversion.base64_to_cv2(b64_str) for b64_str in data['images']]
        results['response'] = antibot_predictor(images)
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
