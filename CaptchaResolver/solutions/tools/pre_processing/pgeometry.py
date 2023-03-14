import numpy as np
import random
import cv2


class Rectangle:
    def __init__(self, rect):
        """
        Rectangle object
        :param rect: [x, y, w, h]
        """
        self.rect = rect

    def xywh(self):
        return self.rect

    def xyxy(self):
        return self.rect[:2] + [self.rect[0] + self.rect[2], self.rect[1] + self.rect[3]]

    def cv2cord(self):
        """
        Convert given rectangle to x1, y1, x2, y2 format
        :return: rect
        """
        x1, y1, x2, y2 = self.rect
        x2 = x1 + x2
        y2 = y1 + y2
        return x1, y1, x2, y2

    def center(self):
        """Get center of rect object"""

        return int((self.rect[0] + self.rect[2]) / 2), int((self.rect[1] + self.rect[3] / 2))

    def expand(self, k_dist, output='self'):
        """
        Expand rectangle::

        :param rect: x1, y1, x2, y2
        :param k_dist: expanding distance or border
        :return: new rectangle
        """

        x1, y1, x2, y2 = self.rect
        x1 -= k_dist
        y1 -= k_dist
        x2 += k_dist + k_dist
        y2 += k_dist + k_dist

        if output == 'self':
            self.rect = [x1, y1, x2, y2]
        else:
            return [x1, y1, x2, y2]

    def shrink(self, k_dist, output='self'):
        """Same as expand with -ve k_distance"""
        return self.expand(-k_dist, output)

    def rangeXY(self):
        """
        Get coordinates
        :param rect: input rectangle
        :return: x, y
        """

        X, Y = set(range(self.rect[0], self.rect[0] + self.rect[2])), set(range(self.rect[1], self.rect[1] + self.rect[3]))
        return X, Y

    def is_overlap(self, rect, filter_duplicate=False):
        """
        Is self_rect overlaps rect
        :param rect: new rectangle
        :param filter_duplicate: filter out duplicates rectangles
        :return: bool
        """
        if filter_duplicate and self.rect == rect.rect:
            return False
        r1, r2 = self.rangeXY(), rect.rangeXY()
        return bool(not r1[0].isdisjoint(r2[0]) and not r1[1].isdisjoint(r2[1]))

    def draw(self, img, color=None, thickness=1):
        """
        Draw rectangle on given image
        :param img: cv2.imread() -> img
        :param color: random if None
        :param thickness: rect thickness
        :return: None
        """

        if color is None:
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        cv2.rectangle(img, self.rect[:2], (self.rect[0] + self.rect[2], self.rect[1] + self.rect[3]), color, thickness)

    @staticmethod
    def show(rects, img=np.zeros([1000, 800, 3]), i=1, thickness=1, position=()):
        """
        See rect changes
        :param rects: [rect, rect, ...]
        :param i: show image after i rect plot
        :param position: move output window there
        :return: None
        """
        _img = img.copy()

        for r, rect in enumerate(rects):
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            cv2.rectangle(_img, rect[:2], (rect[0] + rect[2], rect[1] + rect[3]), color, thickness)
            print(f"Rect draw: {rects[r - 1]} -> {rect}")
            if r % i - 1 == 0 or i == 1:
                cv2.imshow("View", _img)
                if position:
                    cv2.moveWindow("View", *position)
                cv2.waitKey(0)
                cv2.destroyAllWindows()


def rect_overlap(rect1, rect2):
    x1_1, y1_1, x2_1, y2_1 = rect1
    x1_2, y1_2, x2_2, y2_2 = rect2
    return (x1_1 < x2_2) and (x2_1 > x1_2) and (y1_1 < y2_2) and (y2_1 > y1_2)

