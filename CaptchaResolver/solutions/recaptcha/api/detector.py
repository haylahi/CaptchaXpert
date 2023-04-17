import logging
import os.path

import cv2
import yaml
from ultralyticsplus import YOLO

logging.getLogger("ultralyticsplus").setLevel(logging.ERROR)


class Model:
    def __init__(self, model_dir=None, label_dir=None):
        if model_dir is None:
            self.model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'detectors')
            if not os.path.exists(self.model_dir):
                os.mkdir(self.model_dir)
        else:
            self.model_dir = model_dir
        if label_dir is None:
            self.label_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'labels')
        else:
            self.label_dir = label_dir
        self.models = {}
        self.labels = {}
        self.class_names = []
        self._load()

    def _load_classes(self):
        for mn in os.listdir(self.label_dir):
            with open(os.path.join(self.label_dir, mn), 'r') as f:
                self.labels[mn.replace('.yaml', '')] = yaml.safe_load(f)

    def _load_models(self):
        for mn in os.listdir(self.model_dir):
            model = YOLO(os.path.join(self.model_dir, mn))
            model.overrides['iou'] = 0.45
            model.overrides['agnostic_nms'] = False
            model.overrides['max_det'] = 50
            model.overrides['conf'] = 0.2
            self.models[mn.removesuffix('.pt')] = model

    def _load(self):
        self._load_classes()
        self._load_models()

    def choose_net(self, label):
        for k in self.labels.keys():
            if self.labels[k].get('classes') is not None:
                if label in self.labels[k]['classes']:
                    self.class_names = self.labels[k]['classes']
                    return self.models[k]

    def predict(self, img, net, conf=0.2):
        """
        Predict yolo classes for yolov8
        :param img: np_array in cv2 format
        :param net: deep neural network
        :param conf: confidence for object detection
        :return: {'classes': [cls, n], 'boxes': [[x, y, x, y], n], 'scores': [float, n]}
        """

        results = net.predict(img, conf=conf, verbose=False)
        cls = [self.class_names[int(x)] for x in results[0].boxes.cls]
        scores = [float(x) for x in results[0].boxes.conf]
        boxes = [[int(x) for x in box] for box in list(results[0].boxes.xyxy)]
        return {'classes': cls, 'boxes': boxes, 'scores': scores}


if __name__ == '__main__':
    Model().predict(None)
