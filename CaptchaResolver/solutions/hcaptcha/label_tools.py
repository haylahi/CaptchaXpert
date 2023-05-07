import logging
import os
import re

import requests
import yaml

logger = logging.getLogger(__name__)
release_url = "https://github.com/M-Zubair10/CaptchaXpert/releases/download/v2.0/"
map_path = os.path.join(os.path.dirname(__file__), 'label_map.yaml')
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


def pull_map():
    asset_url = os.path.join(release_url, 'label_map.yaml')
    logger.info(f"Pulling label_map.yaml: {asset_url}")
    response = requests.get(asset_url)
    if response.status_code == 200:
        with open(map_path, 'wb') as asset:
            asset.write(response.content)
    else:
        if input(f'Failed to download label_map.yaml from {asset_url}\nContinue [Y/N]? ').lower() == 'y':
            pass
        else:
            raise Exception('Aborted!')


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
        pull_map()
    with open(map_path, 'r') as file:
        LABEL_MAP = yaml.safe_load(file)['MAP']
    return LABEL_MAP
