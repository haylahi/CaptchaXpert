import logging
import os.path

import waitress as waitress
from flask import Flask, request, render_template

if os.path.exists('app.log'):
    os.remove('app.log')

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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


@app.route('/')
def index():
    logger.info("Index page")
    return render_template('index.html')


@app.route('/resolve', methods=['POST', 'GET'])
def captcha_resolver():
    """
    Post examples::
        hcaptcha: {'type': 'hcaptcha', 'images': b64_imgs, 'prompt': 'Please click each image containing a duck.'}
        recaptcha: {'type': 'recaptcha', 'images': b64_imgs, 'label': 'bus', grid: '1x1 or 3x3 or 4x4'}
        antibot: {'type': 'antibot', 'images': b64_imgs}
        viefaucet: {'type': 'vie_antibot', 'images': b64_imgs}
    :return: thread id
    """

    data = request.json
    vdata = data.copy()
    if vdata.get('image') is not None:
        vdata['image'] = '<b64_image>'
    else:
        vdata['images'] = '<b64_images>'
    logger.info(f"[Resolver] {vdata}")
    results = intercept(data)
    return results


if __name__ == '__main__':
    logger.info("Serving on http://127.0.0.1:5000")
    waitress.serve(app, listen='0.0.0.0:5000')
