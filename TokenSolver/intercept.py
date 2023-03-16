import logging
import time

from solutions.api import TokenAPI

logger = logging.getLogger(__name__)


def intercept(data):
    """
    Perform detection
    :param data::
        type: hcaptcha or antibot or viefaucet or recaptcha
        prompt: if hcaptcha or recaptcha(send label)
        images: base64 images
    :return: predictions
    """

    start_time = time.time()
    results = {
        'response': TokenAPI(data['type'], data['url'], data['sitekey'], data['proxy'], int(data['timeout'])).fetch_token()
    }
    end_time = time.time()
    fake_response = 'token' if results['response'] else 'CannotSolveException'
    logger.info(f"Response: {fake_response} | Time-Consumption: {round(end_time - start_time, 2)}")
    return results
