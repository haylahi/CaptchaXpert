import logging
import os.path
import uuid
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, render_template

if os.path.exists('app.log'):
    os.remove('app.log')

logger = logging.getLogger(__name__)
logging.getLogger('seleniumwire').setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s:%(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)

file_handler = logging.FileHandler('app.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.propagate = True

logger.info("Loading solutions...")
from intercept import intercept

logger.info("Everything is ready")

app = Flask(__name__)
threads = {}
thread_pool_executor = ThreadPoolExecutor(max_workers=100)
DEFAULTS = {
    'domain': 'MUST_BE_POSTED',
    'sitekey': 'MUST_BE_POSTED',
    'type': 'MUST_BE_POSTED',
    'visibility': False,
    'enforcer': 1,
    'proxy': None,
    'timeout': 120,
}


@app.route('/')
def index():
    """Render Index page"""
    return render_template('index.html')


@app.route('/submit', methods=['POST', 'GET'])
def captcha_resolver():
    """
    Submit url and sitekey for captcha to be solved
    Note: Timeout range is 0-300 seconds
    :return: thread id
    """

    data = request.json
    for k, v in DEFAULTS.items():
        if k not in data.keys():
            data[k] = DEFAULTS[k]

    missing_params = [k for k, v in data.items() if v == 'MUST_BE_POSTED']
    if missing_params:
        return {"response": "Bad Request", "traceback": f"Following parameters are missing: {' - '.join(missing_params)}"}

    args = (data['type'], data['domain'], data['sitekey'], thread_pool_executor, data['proxy'], int(data['timeout']),
            data['visibility'], data['enforcer'])
    future = thread_pool_executor.submit(intercept, *args)
    thread_id = str(uuid.uuid4())
    threads[thread_id] = future

    logger.info(f"[Submit] {data} | ThreadID: {thread_id}")
    return thread_id


@app.route('/response', methods=['GET'])
def get_response():
    """
    Send thread id to get response
    :return: token
    """

    thread_id = request.args.get('id')
    if threads.get(thread_id) is None:
        return {"response": "NoSuchThreadFoundException"}
    elif not threads[thread_id].done():
        return {"response": "Still solving"}

    response = threads[thread_id].result()
    logger.info(f"[GET] Response: {response} | ThreadID: {thread_id}")
    del threads[thread_id]
    return response


if __name__ == '__main__':
    import waitress as waitress

    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("selenium").setLevel(logging.ERROR)

    logger.info("Serving on http://127.0.0.1:5004 && http://0.0.0.0:5004")
    waitress.serve(app, listen='0.0.0.0:5004')
