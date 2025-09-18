# vision/card_layout.py

# Configuration (use your provided ranges)
TABLEAU_Y_MIN = 310
WASTE_X_MAX = 740
STOCK_X_MAX = 500
FOUNDATION_X_MIN = 880
FOUNDATION_X_MAX = 1600

COLUMN_RANGES = {
    1: (360, 500),
    2: (535, 676),
    3: (712, 854),
    4: (888, 1030),
    5: (1066, 1206),
    6: (1242, 1384),
    7: (1420, 1560),
}


def _tableau_col_for_x(x):
    for col, (xmin, xmax) in COLUMN_RANGES.items():
        if xmin <= x <= xmax:
            return col
    return None


def analyze_layout(detected_cards):
    """
    detected_cards: list of items in either of these forms:
       - (card_name, (x, y))
       - (card_name, (x, y), score)
       - or (card_name, x, y)
    Returns layout dict:
    {
      "stock": [card_name, ...],
      "waste": [card_name, ...],         # left -> right, playable = last
      "foundation": {suit:[...],...},    # suit piles
      "tableau": {1:[...],...,7:[...]}   # bottom->top, playable = last
    }
    """
    # normalize input
    normalized = []
    for entry in detected_cards:
        if not entry:
            continue
        if len(entry) == 3:
            # could be (name, (x,y), score) or (name, x, y)
            name = entry[0]
            second = entry[1]
            third = entry[2]
            if isinstance(second, (tuple, list)) and len(second) == 2:
                x, y = second
            else:
                x, y = second, third
        elif len(entry) == 2 and isinstance(entry[1], (tuple, list)):
            name, (x, y) = entry
        else:
            # unknown format
            continue
        normalized.append((str(name), int(x), int(y)))

    layout = {
        "stock": [],
        "waste": [],
        "foundation": {"h": [], "c": [], "d": [], "s": []},
        "tableau": {i: [] for i in range(1, 8)}
    }

    # temporary lists with coords for sorting
    stock_x = []
    waste_x = []
    foundation_x = {"h": [], "c": [], "d": [], "s": []}
    tableau_by_col = {i: [] for i in range(1, 8)}  # holds tuples (name, y)

    for name, x, y in normalized:
        suit = name[-1].lower()

        # Tableau
        if y >= TABLEAU_Y_MIN:
            col = _tableau_col_for_x(x)
            if col is not None:
                tableau_by_col[col].append((name, y))
            else:
                print(f"[WARNING] {name} at ({x},{y}) not assigned to any tableau column")
            continue

        # Upper row: stock vs waste
        if x <= WASTE_X_MAX:
            if x < STOCK_X_MAX:
                stock_x.append((name, x))
            else:
                waste_x.append((name, x))
            continue

        # Foundation area on right side
        if FOUNDATION_X_MIN <= x <= FOUNDATION_X_MAX:
            if suit in foundation_x:
                foundation_x[suit].append((name, x))
            else:
                print(f"[WARNING] {name} has unknown suit, cannot assign to foundation")
            continue

        # Unclassified
        print(f"[WARNING] Unclassified card {name} at ({x},{y})")

    # Sort and strip coordinates
    stock_x.sort(key=lambda t: t[1])   # left -> right
    waste_x.sort(key=lambda t: t[1])   # left -> right

    layout["stock"] = [c for c, _ in stock_x]
    layout["waste"] = [c for c, _ in waste_x]

    for suit, items in foundation_x.items():
        items.sort(key=lambda t: t[1])  # sort left->right inside area
        layout["foundation"][suit] = [c for c, _ in items]

    # For each tableau column: last element = topmost visible card
    for col in range(1, 8):
        col_list = tableau_by_col[col]
        if not col_list:
            layout["tableau"][col] = []
            continue
        # sort by y descending (lower = deeper row), so topmost is last
        col_list.sort(key=lambda t: t[1], reverse=True)
        layout["tableau"][col] = [name for name, _ in col_list]

    return layout
