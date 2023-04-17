import logging
from collections import Counter

from .api import clean_label, merge_classes, solved_objects
from .api import detector
from ..tools.pre_processing import plist, pimage
from ..tools.pre_processing.pgeometry import rect_overlap, Rectangle

logger = logging.getLogger(__name__)


def predict(img, label, grid):
    label = clean_label(label)
    if label not in solved_objects:
        logger.info(f"Label: {label} not currently solved!")
        return False

    # Inference
    if grid == '3x3':
        imgs = pimage.split(img, structure=(int(grid.split('x')[0]), int(grid.split('x')[1])))
        imgs = plist.transpose(imgs)
        imgs = sum(imgs, [])
        net = detector.choose_net(label)
        results = []
        for img in imgs:
            res = detector.predict(img, net)
            if label in res['classes']:
                results.append(True)
            else:
                if label == 'motorcycle' and 'bicycle' in res['classes']:
                    results.append(True)
                else:
                    results.append(False)

        if Counter(results)[True] < 3:
            logger.info("Return false because len(True) < 3")
            return False
        return results
    elif grid == "1x1":
        imgs = img
        net = detector.choose_net(label)
        results = []
        for img in imgs:
            res = detector.predict(img, net)
            if label in res['classes']:
                results.append(True)
            else:
                if label == 'motorcycle' and 'bicycle' in res['classes']:
                    results.append(True)
                else:
                    results.append(False)
        return results
    else:
        net = detector.models['yolov8s']
        detector.class_names = detector.labels['yolo']['classes']
        detection = detector.predict(img, net)

        # filtering real objects
        if label == 'vehicle':
            detection['classes'] = ['vehicle' if x in merge_classes['vehicles'] else x for x in detection['classes']]
        idx = [i for i in range(len(detection['classes'])) if
               label == detection['classes'][i] or 'vehicle' == detection['classes'][i]]
        classes, boxes = [detection['classes'][i] for i in idx], [detection['boxes'][i] for i in idx]

        if not classes:
            logger.info("Return false because no class is detected by YOLO")
            return False

        # Splitted image size
        spX, spY = img.shape[0] / 4, img.shape[1] / 4

        # Make small images coordinates
        strip = 5
        cord = []
        for m in range(4):
            for n in range(4):
                x, y, w, h = int(spX * n), int(spY * m), int(spX), int(spY)
                c = Rectangle([x, y, w, h])
                c.shrink(strip)
                cord.append(c)

        # Mark if box in small image
        mark_idx = set()
        for i, c in enumerate(cord):
            for b in boxes:
                if rect_overlap(c.xyxy(), b):
                    mark_idx.add(i)
        mark_idx = list(mark_idx)
        return [True if i in mark_idx else False for i in range(16)]
