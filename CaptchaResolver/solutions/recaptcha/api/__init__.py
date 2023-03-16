from .classifier import Model as Classifier
from .detector import Model as Detector
from .label import clean_label, merge_classes, solved_objects

classifier = Classifier()
detector = Detector()

__all__ = ['classifier', 'detector', 'clean_label', 'merge_classes', 'solved_objects']
