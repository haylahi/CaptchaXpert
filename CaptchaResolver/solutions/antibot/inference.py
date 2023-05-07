from ..tools.pre_processing import plist, pimage
from ..tools.common.pull import pull_asset
import os.path

import cv2
import numpy as np
import onnxruntime

release_tag = 'v3.0'
model_name = 'antibot.onnx'
model_path = os.path.join(os.path.dirname(__file__), 'assets', model_name)
if not os.path.exists(model_path):
    pull_asset(release_tag, model_name, os.path.dirname(model_path))
model = onnxruntime.InferenceSession(model_path)
class_names = ['1', '10', '11', '2', '3', '4', '5', '6', '7', '8', '9', 'ant', 'cat', 'cow', 'dog',
               'elephant', 'fox', 'lion', 'monkey', 'mouse', 'nan', 'tiger']


def infer(img: str or np.ndarray, n=1, scores=False):
    """
    Predict labels for antibot-links
    Model expect that the shape of img is (1, 40, 40, 3)
    :param img: img can be a path or ndarray
    :param n: number of predictions needed | n < len(classes) == 22
    :param scores: scores of prediction as a tuple of (prediction, score)
    :return: list of outputs
    """

    if isinstance(img, str):
        img = cv2.imread(img)
        img = cv2.resize(img, (40, 40))
        img = np.reshape(img, (1, 40, 40, 3)).astype(np.float32)

    input_name = model.get_inputs()[0].name
    yhat = model.run(None, {input_name: img})[0][0]
    x_maxN = plist.argmaxN(yhat, n)
    y_maxN = plist.maxN(yhat, n)
    predictions = [(class_names[x_maxN[i]], y_maxN[i]) for i in range(n)]
    if not scores:
        predictions = [x for x, y in predictions]
    return predictions[::-1]


def predict(images):
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
    response = [infer(img, scores=True)[0] for img in images]
    response = [(x[0], str(x[1])) for x in response]
    return response
