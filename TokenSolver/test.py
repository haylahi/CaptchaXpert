from threading import current_thread
from concurrent.futures import ThreadPoolExecutor
import time

import requests

# Get proxy from rotator
# Proxy notation: USER:PASS@IP:PORT
proxy = {
    'protocol': 'http',
    'username': 'afqudxao',
    'password': 'fa0uj3grjt2b',
    'port': 8133,
    'host': '45.155.68.129',
}
recaptcha_data = {
    'type': 'recaptcha-v2',
    'domain': 'nopecha.com',
    'sitekey': '6Ld8NA8jAAAAAPJ_ahIPVIMc0C4q58rntFkopFiA',
    'timeout': 300,
    # 'proxy': proxy,
}
hcaptcha_data = {
        'type': 'hcaptcha',
        'domain': 'nopecha.com',
        'sitekey': 'b4c45857-0e23-48e6-9017-e28fff99ffb2',
        'timeout': 300,
    }


def preprocess(func):
    def wrapper(*args, **kwargs):
        tests_performed = 0
        while tests_performed < NO_OF_TESTS:
            futures = []
            for c in range(CONCURRENCY):
                kwargs['index'] = tests_performed + 1 * c + 1
                future = pool.submit(func, *args, **kwargs)
                futures.append(future)

            while not all([future.done() for future in futures]):
                time.sleep(2)
            tests_performed += CONCURRENCY
    return wrapper


@preprocess
def handle_request(host, data, poll_interval=5, index=None):
    name = current_thread().name
    print(f"{name}: Test-{index} - Posting request...")
    response = requests.get(f"{host}/submit", json=data, timeout=300)
    response_id = response.content.decode('utf-8')
    print(f"{name}: Test-{index} - Response id: {response_id}")
    st = time.time()

    while True:
        response = requests.get(f"{host}/response?id={response_id}", timeout=300).json()
        et = time.time()
        if response['response'] != 'Still solving':
            break
        print(f"{name}: Test-{index} - {response} | Duration: {round(et - st, 3)}")
        time.sleep(poll_interval)

    print(f"{name}: Test-{index} - Your token: {response} | Duration: {round(et - st, 3)}")


def recaptcha_local_test():
    return handle_request(LOCAL_HOST, recaptcha_data)


def recaptcha_remote_test():
    return handle_request(REMOTE_HOST, recaptcha_data)


def hcaptcha_local_test():
    return handle_request(LOCAL_HOST, hcaptcha_data)


def hcaptcha_remote_test():
    return handle_request(REMOTE_HOST, hcaptcha_data)


if __name__ == '__main__':
    LOCAL_HOST = 'http://127.0.0.1:5004'
    REMOTE_HOST = 'http://44.215.184.112:5004'
    NO_OF_TESTS = 5
    CONCURRENCY = 2
    VISIBILITY = False
    ENFORCER = 1

    hcaptcha_data['visibility'] = recaptcha_data['visibility'] = VISIBILITY
    hcaptcha_data['enforcer'] = recaptcha_data['enforcer'] = ENFORCER

    pool = ThreadPoolExecutor(max_workers=CONCURRENCY)
    recaptcha_local_test()
    pool.shutdown()
