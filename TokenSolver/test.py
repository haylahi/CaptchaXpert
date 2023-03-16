import time

import requests

# Get proxy from rotator
proxy = {
    'protocol': 'http',
    'username': 'afqudxao',
    'password': 'fa0uj3grjt2b',
    'port': 8133,
    'host': '45.155.68.129',
}
data = {
    'type': 'recaptcha-v2',
    'url': 'https://nopecha.com/demo/recaptcha',
    'sitekey': '6Ld8NA8jAAAAAPJ_ahIPVIMc0C4q58rntFkopFiA',
    'proxy': proxy,
    'timeout': 40,
}
data = {
        'type': 'hcaptcha',
        'url': 'https://nopecha.com/demo',
        'sitekey': 'b4c45857-0e23-48e6-9017-e28fff99ffb2',
    }
response = requests.get("http://127.0.0.1:5004/submit", json=data)
response_id = response.content.decode('utf-8')
print(f"Response id: {response_id}")

while True:
    response = requests.get(f'http://127.0.0.1:5004/response?id={response_id}').content.decode('utf-8')
    print(response)
    if response != 'Still solving':
        break
    time.sleep(5)

print(f"Your token: {response}")
