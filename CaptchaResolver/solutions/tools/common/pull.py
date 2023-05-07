import os
import logging

import requests

logger = logging.getLogger(__name__)

release_url = "https://github.com/M-Zubair10/CaptchaXpert/releases/download"


def pull_asset(release_tag, asset_name, download_directory):
    asset_url = f"{release_url}/{release_tag}/{asset_name}"
    logger.info(f"Pulling {asset_name}: {asset_url}")
    response = requests.get(asset_url)
    if response.status_code == 200:
        os.makedirs(download_directory, exist_ok=True)
        with open(os.path.join(download_directory, asset_name), 'wb') as asset:
            asset.write(response.content)
    else:
        if input(f'Failed to download {asset_name} from {asset_url}\nContinue [Y/N]? ').lower() == 'y':
            pass
        else:
            raise Exception('Aborted!')
