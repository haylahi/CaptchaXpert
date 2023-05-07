import base64
import io
import sys
import uuid
from collections import Counter

import cv2
import numpy as np
from PIL import Image


def read_all(paths):
    return [cv2.imread(p) for p in paths]


def minMaxLocN(src, template, n=1):
    """
    Fake max and min loc to get second loc and so on
    :param src: result of match template
    :param template: template image which passed to matchTemplate func()
    :param n: number of locs required
    :return: list of locs
    """
    w, h = template.shape[::-1]
    locs = []
    src_h, src_w = src.shape[:2]
    for i in range(n):
        loc = cv2.minMaxLoc(src)
        locs.append(loc)
        maxL = loc[-1]
        x1 = max(maxL[0] - w // 2, 0)
        y1 = max(maxL[1] - h // 2, 0)
        x2 = min(maxL[0] + w // 2, src_w)
        y2 = min(maxL[1] + h // 2, src_h)
        src[y1:y2, x1:x2] = 0
        minL = loc[-2]
        x1 = max(minL[0] - w // 2, 0)
        y1 = max(minL[1] - h // 2, 0)
        x2 = min(minL[0] + w // 2, src_w)
        y2 = min(minL[1] + h // 2, src_h)
        src[y1:y2, x1:x2] = 0
    return locs


def rotate(img, angle, center=None):
    if center is None:
        center = tuple(np.array(img.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, rot_mat, img.shape[1::-1], flags=cv2.INTER_LINEAR)


def contourAVG(cnt, kernel):
    _cnt = []
    for c in range(0, len(cnt), kernel):
        pool = [cnt[c + x] for x in range(kernel) if c + x < len(cnt)]
        avg = [round((sum([x[0][0] for x in pool])) / len(pool)), round((sum([x[0][1] for x in pool])) / len(pool))]
        _cnt.append([avg])
    _cnt = np.array(_cnt)
    return _cnt


def split(img, structure):
    """
    :param img: ndarray
    :param structure: tuple[x, y]
    :return: split images in order [y, x]
    """
    outs = []
    y_diff, x_diff = int(img.shape[0] / structure[1]), int(img.shape[1] / structure[0])
    for x in range(1, structure[0] + 1):
        structuring = []
        for y in range(1, structure[1] + 1):
            res = img[int(y_diff * (y - 1)):int(y_diff * y), int(x_diff * (x - 1)):int(x_diff * x)]
            structuring.append(res)
        outs.append(structuring)
    return outs


def show(*imgs: str or list):
    names = [str(uuid.uuid4()) for _ in range(len(imgs))]
    for i in range(len(imgs)):
        cv2.imshow(names[i], cv2.imread(imgs[i]) if isinstance(imgs[i], str) else imgs[i])
    for n in range(len(names)):
        cv2.moveWindow(names[n], (n + 1) * 200, 100)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def read_base64(path, encoding="bytes"):
    with open(path, "rb") as image_file:
        b64 = base64.b64encode(image_file.read())
    if encoding == 'ascii':
        b64 = b64.decode('ascii')
    return b64


def cv2_to_base64(img: np.ndarray, encoding='bytes'):
    _, im_arr = cv2.imencode('.jpg', img)  # im_arr: image in Numpy one-dim array format.
    im_bytes = im_arr.tobytes()
    b64 = base64.b64encode(im_bytes)
    if encoding == 'ascii':
        b64 = b64.decode('ascii')
    return b64


# def cv2_to_base64(img):
#     return pil_to_base64(Image.fromarray(img))


def base64_to_pil(b64_str):
    return Image.open(io.BytesIO(base64.decodebytes(bytes(b64_str, "utf-8"))))


def base64_to_cv2(b64_str):
    return np.asarray(base64_to_pil(b64_str))  # noqa


def pil_to_bytes(img):
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


def cv2_to_bytes(img):
    return pil_to_bytes(Image.fromarray(img))


def base64_to_bytes(b64_str):
    return pil_to_bytes(base64_to_pil(b64_str))


def is_blank(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    pixels = [img[i, j] for i in range(img.shape[0]) for j in range(img.shape[1])]
    if len(Counter(pixels)) < 10:
        return True


def counterApprox(cnt, epsilon=0.01):
    perimeter = cv2.arcLength(cnt, True)
    epsilon = epsilon * cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, epsilon, True)
    return approx


def center(img):
    return round(img.shape[0] / 2), round(img.shape[1] / 2)


def autoModeOcr(img, config='', strip=False):
    from pytesseract import image_to_string  # Move it to ocr.py
    new_p = 255 - img
    new_p = Image.fromarray(new_p)
    if new_p.mode != 'RGB':
        new_p = new_p.convert('RGB')
    return image_to_string(new_p, config=config) if not strip else image_to_string(new_p, config=config).strip('\n').strip(' ')


def fix_shapes_by_applying_border(img1, img2):
    if img1.shape[0] % 2 != 0:
        img1 = cv2.copyMakeBorder(img1, 0, 1, 0, 0, cv2.BORDER_CONSTANT)
    if img1.shape[1] % 2 != 0:
        img1 = cv2.copyMakeBorder(img1, 0, 0, 1, 0, cv2.BORDER_CONSTANT)
    if img2.shape[0] % 2 != 0:
        img2 = cv2.copyMakeBorder(img2, 0, 1, 0, 0, cv2.BORDER_CONSTANT)
    if img2.shape[1] % 2 != 0:
        img2 = cv2.copyMakeBorder(img2, 0, 0, 1, 0, cv2.BORDER_CONSTANT)
    if img1.shape != img2.shape:
        by, bx = int((img1.shape[0] - img2.shape[0]) / 2), int((img1.shape[1] - img2.shape[1]) / 2)
        if by < 0:
            img1 = cv2.copyMakeBorder(img1, -by, -by, 0, 0, cv2.BORDER_CONSTANT)
        else:
            img2 = cv2.copyMakeBorder(img2, by, by, 0, 0, cv2.BORDER_CONSTANT)
        if bx < 0:
            img1 = cv2.copyMakeBorder(img1, 0, 0, -bx, -bx, cv2.BORDER_CONSTANT)
        else:
            img2 = cv2.copyMakeBorder(img2, 0, 0, bx, bx, cv2.BORDER_CONSTANT)
    return img1, img2


def findContours(img, min_area=0, max_area=sys.maxsize):
    new_img = np.zeros(img.shape)
    cnts = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    cnts = [c for c in cnts if min_area < cv2.contourArea(c) < max_area]
    return cv2.fillPoly(new_img, cnts, 255, cv2.LINE_AA)


def remove_borders(imgs, x_border=True, y_border=True):
    new_imgs = []
    for img in imgs:
        x, y, w, h = cv2.boundingRect(cv2.findNonZero(img))
        if x_border and y_border:
            new_imgs.append(img[y:y + h, x:x + w])
        elif x_border:
            new_imgs.append(img[:, x:x + w])
        elif y_border:
            new_imgs.append(img[y:y + h, :])
    return new_imgs
