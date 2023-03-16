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
        self._load()

    def _load_classes(self):
        for mn in os.listdir(self.label_dir):
            with open(os.path.join(self.label_dir, mn), 'r') as f:
                self.labels[mn.replace('.yaml', '')] = yaml.safe_load(f)

    def _load(self):
        for mn in os.listdir(self.model_dir):
            net = cv2.dnn.readNetFromONNX(os.path.join(self.model_dir, mn))
            self.models[mn.replace('.onnx', '')] = net

        self._load_classes()
        # load yolov8
        model = YOLO('ultralyticsplus/yolov8s')
        model.overrides['iou'] = 0.45  # NMS IoU threshold
        model.overrides['agnostic_nms'] = False  # NMS class-agnostic
        model.overrides['max_det'] = 1000  # maximum number of detections per image

        self.models['yolov8'] = {'model': model, 'threshold': 0.15}

    def predict(self, img, version=8):
        """
        Predict yolo classes either yolo_v3 or yolov6 or yolov8
        :param img: np_array in cv2 format
        :param version: specify yolo version (3, 6 or 8)
        :return: {'classes': [cls, n], 'boxes': [[x, y, x, y], n], 'scores': [float, n]}
        """

        model = self.models[f'yolov{version}']
        net = model['model']
        class_names = self.labels['yolo']['classes']
        class_names = [x.replace(' ', '_') for x in class_names]
        threshold = model.get('threshold')
        if version == 8:
            net.overrides['conf'] = threshold  # NMS confidence threshold
            results = net.predict(img)
            cls = [class_names[int(x)] for x in results[0].boxes.cls]
            scores = [float(x) for x in results[0].boxes.conf]
            boxes = [[int(x) for x in box] for box in list(results[0].boxes.xyxy)]
            return {'classes': cls, 'boxes': boxes, 'scores': scores}


if __name__ == '__main__':
    Model().predict(None)
