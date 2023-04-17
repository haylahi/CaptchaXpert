import os

import yaml

recaptcha_objects_yaml = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'labels', 'alias.yaml')
with open(recaptcha_objects_yaml) as f:
    aliases = yaml.safe_load(f)

solved_objects_yaml = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'labels', 'objects.yaml')
with open(solved_objects_yaml) as f:
    solved_objects = yaml.safe_load(f)['Solved']
grounded_objects = ['bridge', 'stair', 'tractor', 'boat', 'chimney']
merge_classes = {
    'vehicles': ['car', 'bicycle', 'motorcycle', 'bus', 'truck', 'boat']
}


def clean_label(label):
    for key, val in aliases.items():
        if label in val:
            return key
    return label
