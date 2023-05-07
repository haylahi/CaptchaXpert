from .detector import Detector, Label

detector = Detector()
label_manager = Label(detector.label_path)


__all__ = ['detector', 'label_manager']
