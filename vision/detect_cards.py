# vision/detect_cards.py
import os
import cv2
import numpy as np

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates", "faces")

# Tuneable thresholds
MATCH_THRESHOLD = 0.75   # template match threshold
NMS_IOU_THRESH = 0.35   # IoU threshold for NMS


def load_templates():
    templates = {}
    for fname in os.listdir(TEMPLATE_DIR):
        if not fname.lower().endswith(".png"):
            continue
        name = os.path.splitext(fname)[0]
        path = os.path.join(TEMPLATE_DIR, fname)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        templates[name] = img
    return templates


def _boxes_iou(boxA, boxB):
    # box = (x1, y1, x2, y2)
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    union = boxAArea + boxBArea - interArea
    if union == 0:
        return 0.0
    return float(interArea) / float(union)


def non_max_suppression(detections, iou_thresh=NMS_IOU_THRESH):
    """
    detections: list of tuples (name, (x, y), score, w, h)
    returns: filtered list of same format (keeps highest-score boxes)
    """
    if not detections:
        return []

    boxes = []
    for det in detections:
        name, (x, y), score, w, h = det
        x1, y1, x2, y2 = x, y, x + w, y + h
        boxes.append((x1, y1, x2, y2, score, name, w, h))

    # Sort by score descending
    boxes = sorted(boxes, key=lambda b: b[4], reverse=True)
    picked = []
    while boxes:
        current = boxes.pop(0)
        picked.append(current)
        boxes = [b for b in boxes if _boxes_iou(current[:4], b[:4]) <= iou_thresh]

    # Convert back to original format
    out = []
    for x1, y1, x2, y2, score, name, w, h in picked:
        out.append((name, (int(x1), int(y1)), float(score), int(w), int(h)))
    return out


def consolidate_same_location(detections, bucket_size=6):
    """
    If multiple different card names overlap at essentially the same location
    (e.g., same top-left), keep only the highest score one.
    bucket_size: group nearby coordinates to same bucket to handle tiny offsets.
    detections: list of (name, (x,y), score, w, h)
    returns list of (name, (x,y), score, w, h)
    """
    buckets = {}
    for name, (x, y), score, w, h in detections:
        key = (round(x / bucket_size), round(y / bucket_size))
        existing = buckets.get(key)
        if existing is None or score > existing[2]:
            buckets[key] = (name, (x, y), score, w, h)
    return list(buckets.values())


def detect_cards(screenshot_path):
    """
    Main detection entry point.
    Returns: list of (card_name, (x, y), score)
    where (x, y) is the detected top-left of the matched template.
    """
    templates = load_templates()
    if not templates:
        return []

    image = cv2.imread(screenshot_path)
    if image is None:
        raise FileNotFoundError(f"Unable to read screenshot: {screenshot_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h_img, w_img = gray.shape

    raw_detections = []
    for name, tmpl in templates.items():
        th, tw = tmpl.shape[:2]
        # If template larger than image, skip
        if th > h_img or tw > w_img:
            continue
        # match
        res = cv2.matchTemplate(gray, tmpl, cv2.TM_CCOEFF_NORMED)
        # find locations above threshold
        loc = np.where(res >= MATCH_THRESHOLD)
        for pt in zip(*loc[::-1]):  # pt = (x, y)
            x, y = pt
            score = float(res[y, x])
            raw_detections.append((name, (int(x), int(y)), score, tw, th))

    # If nothing above threshold, optionally lower threshold slightly (optional)
    # but be conservative to avoid false positives.

    # First stage NMS (IoU-based) to remove overlapping boxes across all templates
    nms_filtered = non_max_suppression(raw_detections, iou_thresh=NMS_IOU_THRESH)

    # Then consolidate multiple names that still map to same location (winner takes all)
    consolidated = consolidate_same_location(nms_filtered, bucket_size=6)

    # Return final simplified format (name, (x,y), score)
    final = [(name, (x, y), score) for (name, (x, y), score, w, h) in consolidated]
    return final
