from .detector import Model as Detector

detector = Detector()

from .label import clean_label, merge_classes, solved_objects, grounded_objects


__all__ = ['detector', 'clean_label', 'merge_classes', 'solved_objects', 'grounded_objects']
