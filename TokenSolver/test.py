import time

import requests

data = {
    'type': 'recaptcha-v2',
    'url': 'https://www.google.com/recaptcha/api2/demo',
    'sitekey': '6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-',
}
response = requests.get("http://127.0.0.1:5004/submit", json=data)
response_id = response.content.decode('utf-8')
print(f"Response id: {response_id}")

while True:
    response = requests.get(f'http://127.0.0.1:5004/response?id={response_id}').content.decode('utf-8')
    if response != 'Still solving':
        break
    time.sleep(5)

print(f"Your token: {response}")
