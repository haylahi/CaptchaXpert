import logging
from ..tools.pre_processing import plist, pimage
from ..tools.pre_processing.pgeometry import rect_overlap, Rectangle

import numpy as np

from .api import classifier
from .api import detector
from .api import clean_label, merge_classes, solved_objects
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
        results = [classifier.predict(img, label, scores=True) for img in imgs]
        resp, scores = [res[0] for res in results], [res[1] for res in results]
        if len([x for x in resp if x]) < 3:
            logger.info("Return false because len(resp == True) < 3")
            return False

        max_idx = plist.argmaxN(np.array(scores), 3)
        return [True if i in max_idx else False for i in range(9)]
    elif grid == "1x1":
        imgs = img
        results = [classifier.predict(img, label) for img in imgs]
        return results
    else:
        detection = detector.predict(img, version=8)

        # filtering real objects
        if label == 'vehicle':
            detection['classes'] = ['vehicle' if x in merge_classes['vehicles'] else x for x in detection['classes']]
        idx = [i for i in range(len(detection['classes'])) if label == detection['classes'][i] or 'vehicle' == detection['classes'][i]]
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

