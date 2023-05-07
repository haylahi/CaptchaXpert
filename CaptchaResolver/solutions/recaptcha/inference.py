import logging

import numpy as np

from .api import label_manager
from .api import detector
from ..tools.pre_processing import plist, pimage
from ..tools.pre_processing.pgeometry import Rectangle

logger = logging.getLogger(__name__)


def predict(img, label, grid):
    label = label_manager.clean_label(label)
    if label not in label_manager.objects:
        logger.info(f"Label: {label} not currently solved!")
        return False

    # Inference
    if grid == '3x3':
        imgs = pimage.split(img, structure=(int(grid.split('x')[0]), int(grid.split('x')[1])))
        imgs = plist.transpose(imgs)
        imgs = sum(imgs, [])
        net = detector.choose_net_3x3(label)
        print(net, label)
        # Inference and get top 3 predictions
        scores = []
        for img in imgs:
            detection = detector.predict(img, net, conf=0.25, verbose=False)
            if label == 'motorcycle' and 'bicycle' in detection['classes']:
                detection['classes'][detection['classes'].index('bicycle')] = 'motorcycle'
            if label in detection['classes']:
                score = detection['scores'][detection['classes'].index(label)]
            else:
                score = 0
            scores.append(score)

        max_indices = plist.argmaxN(np.array(scores), 3)
        if len(max_indices) < 3:
            logger.info("Return false because len(True) < 3")
            return False

        results = [True if x in max_indices else False for x in range(9)]
        return results
    elif grid == "1x1":
        imgs = img
        net = detector.choose_net_3x3(label)
        results = []
        for img in imgs:
            res = detector.predict(img, net, conf=0.3)
            if label in res['classes']:
                results.append(True)
            else:
                if label == 'motorcycle' and 'bicycle' in res['classes']:
                    results.append(True)
                else:
                    results.append(False)
        return results
    else:
        net = detector.choose_net_4x4(label)
        detection = detector.predict(img, net, conf=0.2, verbose=True)

        # filtering real objects
        if label in label_manager.merge_objects.keys():
            detection['classes'] = [label if x in label_manager.merge_objects[label] else x for x in detection['classes']]
        idx = [i for i in range(len(detection['classes'])) if label == detection['classes'][i]]
        if not idx:
            logger.info("Return false because no class is detected by YOLO")
            return False

        H, W = img.shape[0], img.shape[1]
        segments = [detection['masks'].segments[i] for i in idx]
        segmentations = []
        for segment in segments:
            segment[:, 0] = segment[:, 0] * W
            segment[:, 1] = segment[:, 1] * H
            segmentation = [segment.ravel().tolist()]
            points = [np.array(point).reshape(-1, 2).round().astype(int) for point in segmentation]
            segmentations.append(points)

        # Make small images coordinates
        coordinates = []
        spX, spY = img.shape[0] / 4, img.shape[1] / 4
        for m in range(4):
            for n in range(4):
                x, y, w, h = int(spX * n), int(spY * m), int(spX), int(spY)
                c = Rectangle([x, y, w, h])
                coordinates.append(c)

        # segment to contours
        blank_img = np.zeros(img.shape)
        color = (0, 0, 255)
        for segment in segmentations:
            pimage.draw_mask(blank_img, segment, color=color)
        indices = np.where((blank_img == [0, 0, 255]).all(axis=2))
        points = [np.array([x, y]) for y, x in zip(indices[0], indices[1])]

        # Mark if point in object
        results = []
        for c in coordinates:
            is_in = False
            for p in points:
                if c.in_point(p):
                    is_in = True
                    break
            if not is_in:
                for segment in segmentations:
                    if c.in_mask(segment[0]):
                        is_in = True
                        break
            results.append(is_in)

        return results
