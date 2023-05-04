import logging
import os.path

import requests
import yaml
from ultralyticsplus import YOLO

logging.getLogger("ultralyticsplus").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

ASSETS = ['re-detector-v1.pt', 're-detector-v2.pt', 'yolov8s-seg.pt', 'crosswalk-seg.pt', 'stair-seg.pt',
          'yolo.yaml', 'objects.yaml', 'alias.yaml', 're-detector-v1.yaml', 're-detector-v2.yaml', ]


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
            if not os.path.exists(self.label_dir):
                os.mkdir(self.label_dir)
        else:
            self.label_dir = label_dir
        self.models = {}
        self.labels = {}
        self.class_names = []
        self.release_url = 'https://github.com/M-Zubair10/CaptchaXpert/releases/download/v1.0/'
        self._pull()
        self._load()

    def _pull_asset(self, asset_name, local_storage_dir):
        asset_url = os.path.join(self.release_url, asset_name)
        logger.info(f"Pulling {asset_name}: {asset_url}")
        response = requests.get(asset_url)
        if response.status_code == 200:
            with open(os.path.join(local_storage_dir, asset_name), 'wb') as asset:
                asset.write(response.content)
        else:
            if input(f'Failed to download {asset_name} from {asset_url}\nContinue [Y/N]? ').lower() == 'y':
                pass
            else:
                raise Exception('Aborted!')

    def _pull(self):
        for asset_name in ASSETS:
            if asset_name.endswith('.pt') or asset_name.endswith('.onnx'):
                local_storage_dir = self.model_dir
            elif asset_name.endswith('.yaml'):
                local_storage_dir = self.label_dir
            else:
                raise Exception('Unknown asset')

            if not os.path.exists(os.path.join(local_storage_dir, asset_name)):
                self._pull_asset(asset_name, local_storage_dir)

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
            model.overrides['conf'] = 0.25
            self.models[mn.removesuffix('.pt')] = model

    def _load(self):
        self._load_classes()
        self._load_models()

    def choose_net_3x3(self, label):
        for k in self.labels.keys():
            if self.labels[k].get('classes') is not None:
                if label in self.labels[k]['classes']:
                    self.class_names = self.labels[k]['classes']
                    return self.models[k]

    def choose_net_4x4(self, label):
        net = self.models['yolov8s-seg']
        self.class_names = self.labels['yolo']['classes']
        if label == 'stair':
            net = self.models['stair-seg']
            self.class_names = ['stair']
        elif label == 'crosswalk':
            net = self.models['crosswalk-seg']
            self.class_names = ['crosswalk']
        return net

    def predict(self, img, net, conf=0.2, verbose=False):
        """
        Predict yolo classes for yolov8
        :param verbose: show details
        :param img: np_array in cv2 format
        :param net: deep neural network
        :param conf: confidence for object detection
        :return: {'classes': [cls, n], 'boxes': [[x, y, x, y], n], 'scores': [float, n]}
        """

        results = net.predict(img, conf=conf, verbose=verbose)
        cls = [self.class_names[int(x)] for x in results[0].boxes.cls]
        scores = [float(x) for x in results[0].boxes.conf]
        boxes = [[int(x) for x in box] for box in list(results[0].boxes.xyxy)]
        masks = results[0].masks
        return {'classes': cls, 'boxes': boxes, 'scores': scores, 'masks': masks}
