import os.path
from ...tools.pre_processing import plist

import cv2


class Model:
    def __init__(self, model_dir=None):
        if model_dir is None:
            self.model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'classifiers')
        else:
            self.model_dir = model_dir
        self.models = {}
        self._load()

    def _load(self):
        for mn in os.listdir(self.model_dir):
            net = cv2.dnn.readNetFromONNX(os.path.join(self.model_dir, mn))
            self.models[mn.replace('.onnx', '')] = net

    def predict(self, img, label, scores=False):
        """
        Make inference on input data
        :param img: input image in cv2 format
        :param label: input label
        :param scores: True if scores of True value needed else False
        :return: bool or tuple(bool, float)
        """

        img = cv2.resize(img, (64, 64))
        blob = cv2.dnn.blobFromImage(img, 1 / 255.0, (64, 64), (0, 0, 0), swapRB=True, crop=False)
        net = self.models[label]
        net.setInput(blob)
        out = net.forward()
        x_max = plist.argmaxN(out[0], n=1)[0]
        if scores:
            return x_max == 0, out[0][0]
        return bool(plist.argmaxN(out[0], n=1)[0] == 0)

