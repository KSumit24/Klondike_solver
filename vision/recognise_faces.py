import cv2
import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates", "faces")


def load_templates():
    templates = {}
    for fname in os.listdir(TEMPLATE_DIR):
        if fname.endswith(".png"):
            path = os.path.join(TEMPLATE_DIR, fname)
            templates[fname[:-4]] = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return templates


def recognise_faces(rois, templates, threshold=0.7):
    """Recognise cards inside cropped ROIs."""
    matches = []
    for (x, y, w, h), roi in rois:
        roi_resized = cv2.resize(roi, (100, 140))
        for name, template in templates.items():
            resized_template = cv2.resize(template, (100, 140))
            res = cv2.matchTemplate(roi_resized, resized_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val >= threshold:
                matches.append((name, (x, y)))
    return matches
