import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import logging
import numpy as np
from transformers import CLIPProcessor, CLIPModel
from .label_tools import split_prompt_message, label_cleaning, init_map

logger = logging.getLogger(__name__)

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
LABEL_MAP = init_map(update=True)


def predict(prompt, images):
    """
    Inference on input images
    :param prompt: hcaptcha challenge prompt
    :param images: list of images in PIL.Image format
    :return:
    """
    global LABEL_MAP

    _label = split_prompt_message(prompt)
    label = label_cleaning(_label)
    if label not in LABEL_MAP.keys():
        logger.error(f"The label [{label}] is not yet mapped!")
        LABEL_MAP = init_map(update=True)
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
