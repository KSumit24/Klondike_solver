# automation/move_execute.py
import pyautogui
import time

# -------------------- Coordinates --------------------
FOUNDATION_COORDS = {
    "hearts": (960, 200),
    "clubs": (1135, 200),
    "diamonds": (1310, 200),
    "spades": (1490, 200),
}

STOCK_POS = (460, 200)
WASTE_POS = (599, 193)  # center where all waste cards intersect

TABLEAU_COORDS = {
    1: (430, 400),
    2: (605, 400),
    3: (780, 400),
    4: (955, 400),
    5: (1130, 400),
    6: (1305, 400),
    7: (1480, 400),
}

TABLEAU_Y_OFFSET = 40

# -------------------- Helpers --------------------
def drag_card(src_pos, dest_pos):
    """Drag card from src_pos to dest_pos on screen."""
    x1, y1 = src_pos
    x2, y2 = dest_pos
    pyautogui.moveTo(x1, y1, duration=0.2)
    pyautogui.mouseDown()
    time.sleep(0.1)
    pyautogui.moveTo(x2, y2, duration=0.3)
    pyautogui.mouseUp()
    time.sleep(0.2)

def double_click(pos):
    """Double-click a card at pos."""
    x, y = pos
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.click()
    time.sleep(0.05)
    pyautogui.click()
    time.sleep(0.2)

# -------------------- Move Executor --------------------
def execute_move(move, game_state):
    """
    Execute a move on the screen and update the GameState.
    Moves can be:
      - stock_to_waste
      - waste_to_tableau
      - waste_to_foundation
      - tableau_to_foundation
      - tableau_to_tableau
    """
    try:
        move_type = move.get("type")

        # ---------------- Stock ----------------
        if move_type == "stock_to_waste":
            pyautogui.click(STOCK_POS)
            time.sleep(0.3)
            return

        # ---------------- Waste -> Tableau ----------------
        elif move_type == "waste_to_tableau":
            if not game_state.waste:
                return
            top_card = game_state.waste[-1]
            from_pos = game_state.card_positions.get(top_card, WASTE_POS)
            to_col = move.get("to_column")
            dest_stack = game_state.tableau.get(to_col, [])
            if dest_stack:
                last_card = dest_stack[-1]
                last_pos = game_state.card_positions.get(last_card, TABLEAU_COORDS[to_col])
                to_pos = (TABLEAU_COORDS[to_col][0], last_pos[1] + TABLEAU_Y_OFFSET)
            else:
                to_pos = TABLEAU_COORDS[to_col]
            drag_card(from_pos, to_pos)
            game_state.tableau[to_col].append(top_card)
            game_state.waste.pop()

        # ---------------- Waste -> Foundation ----------------
        elif move_type == "waste_to_foundation":
            if not game_state.waste:
                return
            # Always click at fixed center of waste pile
            double_click(WASTE_POS)
            top_card = game_state.waste[-1]
            game_state.move_to_foundation(top_card)

        # ---------------- Tableau -> Foundation ----------------
        elif move_type == "tableau_to_foundation":
            from_col = move.get("from_column")
            sequence = move.get("sequence", [])
            if not sequence or not from_col:
                return

            card_name = sequence[-1]  # top card

            # Ensure position
            from_pos = game_state.card_positions.get(card_name)
            if not from_pos:
                # fallback: column center + depth
                col_cards = game_state.tableau.get(from_col, [])
                if card_name in col_cards:
                    depth = col_cards.index(card_name)
                    x = TABLEAU_COORDS.get(from_col, (430, 400))[0]
                    y = 310 + depth * TABLEAU_Y_OFFSET
                    from_pos = (x, y)
                else:
                    from_pos = TABLEAU_COORDS.get(from_col, (430, 400))

            # Slight offset
            from_pos = (from_pos[0] + 5, from_pos[1] + 5)

            # Move mouse
            pyautogui.moveTo(from_pos[0], from_pos[1], duration=0.15)
            pyautogui.click()
            time.sleep(0.2)  # allow GUI to register click

            # Update GameState immediately
            game_state.move_to_foundation(card_name)
            if card_name in game_state.tableau.get(from_col, []):
                game_state.tableau[from_col].remove(card_name)

        # ---------------- Tableau -> Tableau ----------------
        elif move_type == "tableau_to_tableau":
            from_col = move.get("from_column")
            to_col = move.get("to_column")
            sequence = move.get("sequence", [])
            if not sequence or not from_col or not to_col:
                return
            moving_card = sequence[0]

            from_pos = game_state.card_positions.get(moving_card)
            if not from_pos:
                from_pos = TABLEAU_COORDS[from_col]

            dest_stack = game_state.tableau.get(to_col, [])
            if dest_stack:
                last_card = dest_stack[-1]
                last_pos = game_state.card_positions.get(last_card, TABLEAU_COORDS[to_col])
                to_pos = (TABLEAU_COORDS[to_col][0], last_pos[1] + TABLEAU_Y_OFFSET)
            else:
                to_pos = TABLEAU_COORDS[to_col]

            drag_card(from_pos, to_pos)
            game_state.move_tableau_to_tableau(sequence, from_col, to_col)

        else:
            print(f"[WARN] Unknown move type: {move_type}")

    except Exception as e:
        import traceback
        print("[ERROR] execute_move() exception:")
        print(traceback.format_exc())
