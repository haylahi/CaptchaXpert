import logging
import os.path

import requests.exceptions

from .precompiled_solution import hcaptcha as solver

logger = logging.getLogger(__name__)

# Init local-side of the ModelHub
workspace = os.path.join(os.path.dirname(__file__), 'workspace')
try:
    solver.install()
except requests.exceptions.ConnectionError:
    logger.critical("Failed to update hcaptcha")


def predict(prompt, images):
    challenger = solver.new_challenger(dir_workspace=workspace)
    if result := challenger.classify(prompt=prompt, images=images):
        return [result[i] for i, fp in enumerate(images)]
