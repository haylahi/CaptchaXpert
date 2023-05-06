import logging
import os
import re

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import numpy as np
import yaml
from transformers import CLIPProcessor, CLIPModel

logger = logging.getLogger(__name__)
BAD_CODE = {
    "а": "a",
    "е": "e",
    "e": "e",
    "i": "i",
    "і": "i",
    "ο": "o",
    "с": "c",
    "ԁ": "d",
    "ѕ": "s",
    "һ": "h",
    "у": "y",
    "р": "p",
    "ー": "一",
    "土": "士",
}
with open(os.path.join(os.path.dirname(__file__), 'label_map.yaml'), 'r') as file:
    LABEL_MAP = yaml.safe_load(file)['MAP']
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


def label_cleaning(raw_label: str) -> str:
    """cleaning errors-unicode"""
    clean_label = raw_label
    for c in BAD_CODE:
        clean_label = clean_label.replace(c, BAD_CODE[c])
    return clean_label


def split_prompt_message(prompt_message: str) -> str:
    """Detach label from challenge prompt"""
    prompt_message = prompt_message.replace(".", "").lower()
    if "containing" in prompt_message:
        return re.split(r"containing a", prompt_message)[-1][1:].strip()
    if "select all" in prompt_message:
        return re.split(r"all (.*) images", prompt_message)[1].strip()
    return prompt_message


def predict(prompt, images):
    """
    Inference on input images
    :param prompt: hcaptcha challenge prompt
    :param images: list of images in PIL.Image format
    :return:
    """
    _label = split_prompt_message(prompt)
    label = label_cleaning(_label)
    if label not in LABEL_MAP.keys():
        logger.error(f"The label [{label}] is not yet mapped!")
        # Send email only once here just to notify me
        return False

    class_names = LABEL_MAP[label]
    results = []
    for image in images:
        inputs = processor(text=class_names, images=image, return_tensors="pt", padding=True)
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
        np_prob = probs.detach().numpy()
        prediction = class_names[np.argmax(np_prob)]
        results.append(prediction == label)
    return results
