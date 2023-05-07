import logging
import os
import re
from ..tools.common.pull import pull_asset

import yaml

logger = logging.getLogger(__name__)
release_tag = 'v2.0'
map_name = 'label_map.yaml'
map_path = os.path.join(os.path.dirname(__file__), 'assets', map_name)
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


def init_map(update=False):
    if not os.path.exists(map_path) or update:
        pull_asset(release_tag, map_name, os.path.dirname(map_path))
    with open(map_path, 'r') as file:
        LABEL_MAP = yaml.safe_load(file)['MAP']
    return LABEL_MAP
