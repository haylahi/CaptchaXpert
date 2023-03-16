import numpy as np
from PIL import Image
import base64
import io
import cv2


def dict2str(dic, beforeK='', afterK=' ', afterV=' ', beforeLK=None, afterLK=None, afterLV=None) -> str:
    """
    Convert dictionary to string::
        General form: {beforeK}{k}{afterK}{v}{afterV} && {k}{afterLK}{v}{afterLV}
        sample: dict2str({'1': 'one', '2': 'two'}, beforeK='--')
                output="--1 one --2 two"
    :param dic: input dictionary
    :param beforeK: value to push before every key, default=''
    :param afterK: value to push after every key, default=' '
    :param afterV: value to push after every value, default=' '
    :param afterLK: value to push after last key, default=afterK
    :param afterLV: value to push after last value, default=afterV
    :param beforeLK: value to push before last key, default=beforeK
    :return: string object from dictionary
    """

    if beforeLK is None:
        beforeLK = beforeK
    if afterLK is None:
        afterLK = afterK
    if afterLV is None:
        afterLV = afterV

    res_str = ""
    for i, k, v in zip(range(len(dic) - 1), list(dic.keys())[:-1], list(dic.values())[:-1]):
        res_str += f"{beforeK}{k}{afterK}{v}{afterV}"

    res_str += f"{beforeLK}{list(dic.keys())[-1]}{afterLK}{list(dic.values())[-1]}{afterLV}"

    return res_str


def str2dict(string):
    """
    Convert given str to dict object
    :param string: input string | '{name: hello, 1:2}'
    :return: dict
    """
    
    return eval(string)
    

def str2int(string_to_convert):
    """
    Convert string to int
    :param string_to_convert: string to be converted
    :return: int or None in case cannot be converted to int
    """

    try:
        return int(string_to_convert)
    except (ValueError, TypeError):
        return None


def int2str(integer):
    """
    Convert integer to string
    :param integer: input int
    :return: str object
    """
    
    return str(integer)


def str2float(string_to_convert):
    """
    Convert string to float
    :param string_to_convert: string to be converted
    :return: float or None in case cannot be converted to float
    """

    try:
        return float(string_to_convert)
    except (ValueError, TypeError):
        return None
    
    
def LIST2list(list_of_items: list):
    """
    Lower-case all list
    :param list_of_items: input list
    :return: list
    """
    
    return [x.lower() for x in list_of_items.copy()]


def list2LIST(list_of_items: list):
    """
    Upper-case all list
    :param list_of_items: input list
    :return: list
    """
    
    return [x.upper() for x in list_of_items.copy()]


def path_to_base64(path, encoding="bytes"):
    """ Read the given path to base64 string """
    with open(path, "rb") as image_file:
        b64 = base64.b64encode(image_file.read())
    if encoding == 'ascii':
        b64 = b64.decode('ascii')
    return b64


def cv2_to_base64(img: np.ndarray, encoding='bytes'):
    """ Convert cv2 image to base64 string """
    _, im_arr = cv2.imencode('.jpg', img)  # im_arr: image in Numpy one-dim array format.
    im_bytes = im_arr.tobytes()
    b64 = base64.b64encode(im_bytes)
    if encoding == 'ascii':
        b64 = b64.decode('ascii')
    return b64


def cv2_to_pil(img):
    """ Convert cv2 image to pil image """
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(np.uint8(img))
    return img_pil


def base64_to_pil(b64_str):
    """ Convert base64 string to pil image """
    return Image.open(io.BytesIO(base64.decodebytes(bytes(b64_str, "utf-8"))))


def base64_to_cv2(b64_str):
    """ Convert base64 string to cv2 image """
    return np.asarray(base64_to_pil(b64_str))   # noqa


def pil_to_bytes(img):
    """ Convert pil image to bytes string """
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


def cv2_to_bytes(img):
    """ Convert cv2 image to bytes string """
    return pil_to_bytes(Image.fromarray(img))


def base64_to_bytes(b64_str):
    """ Convert base64 string to bytes string """
    return pil_to_bytes(base64_to_pil(b64_str))


def imgs2video(images, output_path, fps=30.0):
    """ Convert a list of imgs[path] to a video """

    # Set the video codec and create the video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = None

    # Add each image to the video
    for image in images:
        # Read the image and get its size
        img = cv2.imread(image)
        height, width = img.shape[:2]

        # Create the video writer if it doesn't exist
        if out is None:
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Write the image to the video
        out.write(img)

    # Release the video writer
    out.release()





    
    