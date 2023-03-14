from ..tools.pre_processing import plist
import os.path

import cv2
import numpy as np
import onnxruntime

model_path = os.path.join(os.path.dirname(__file__), 'antibot.onnx')
model = onnxruntime.InferenceSession(model_path)
class_names = ['1', '10', '11', '2', '3', '4', '5', '6', '7', '8', '9', 'ant', 'cat', 'cow', 'dog',
               'elephant', 'fox', 'lion', 'monkey', 'mouse', 'nan', 'tiger']


def predict(img: str or np.ndarray, n=1, scores=False):
    """
    Predict labels for btcbunch.com
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
