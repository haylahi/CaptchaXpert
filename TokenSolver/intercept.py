import logging
import threading
import time

from solutions.api import TokenAPI

logger = logging.getLogger(__name__)


def enforced_token_fetcher(captcha_type, domain, sitekey, proxy, visibility, timeout, executor, is_token_processed):
    """ Run this in thread, to get token """
    return TokenAPI(
        captcha_type=captcha_type,
        domain=domain,
        data_sitekey=sitekey,
        proxy=proxy,
        visibility=visibility,
        timeout=timeout,
        executor=executor
    ).fetch_token(is_token_processed)


def intercept(captcha_type, domain, sitekey, executor, proxy=None, timeout=120, visibility=False, enforcer=1):
    """
    Intercept request
    :param captcha_type: type of captcha, either 'hcaptcha' or 'recaptcha'
    :param domain: domain of target website
    :param sitekey: sitekey of target captcha
    :param executor: ThreadPoolExecutor object from concurrent futures
    :param proxy: format PROTOCOL://USER:PASS@IP:PORT or PROTOCOL://IP:PORT
    :param timeout: maximum time allowed solving captcha
    :param visibility: solve captcha in gui mode or gui-less
    :param enforcer: solve no of captchas concurrently, but immediately close other instances ASAP token found
    :return: dict("response": "token" or "UNKNOWN" in case of unexpected exit or "TimeoutException" in case time limit exceeds)
    """

    start_time = time.time()
    is_token_processed = threading.Event()

    # Executing same job n times
    futures = []
    for e in range(enforcer):
        future = executor.submit(enforced_token_fetcher, captcha_type, domain, sitekey, proxy,
                                 visibility, timeout, executor, is_token_processed)
        futures.append(future)

    # Wait for all futures to complete their jobs
    results = [future.result() for future in futures]
    token = [x.removeprefix('Token-') for x in results if x.startswith('Token')]

    response = {
        'response': token[0] if token else results[0],
        'duration': time.time() - start_time,
    }

    fake_response = 'token' if token else results[0]
    logger.info(f"Response: {fake_response} | Time-Consumption: {round(response['duration'], 3)}")
    return response
