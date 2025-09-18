# main.py
import time
import os
import importlib
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def run_game_loop():
    """
    Continuously plays the Solitaire game until no valid moves remain.
    """
    # Import modules fresh
    from capture.screen_capture import take_screenshot
    from vision.detect_cards import detect_cards
    from vision.card_layout import analyze_layout
    from logic.game_state import GameState
    from logic.move_generator import MoveGenerator
    from automation.move_executor import execute_move

    game_state = None

    while True:
        # 1️⃣ Capture screenshot
        logging.info("Capturing screenshot...")
        screenshot_path = take_screenshot()

        # 2️⃣ Detect visible cards (waste, tableau, foundation)
        logging.info("Detecting visible cards...")
        try:
            detected_cards = detect_cards(screenshot_path)
        except Exception as e:
            logging.error("detect_cards() exception: %s", e)
            time.sleep(2)
            continue

        logging.info("Detected %d cards.", len(detected_cards))
        for c in detected_cards:
            logging.info("  %s at %s (score %.2f)", c[0], c[1], c[2])

        # Build positions dict
        card_positions = {name: pos for (name, pos, score) in detected_cards}

        # 3️⃣ Analyze layout
        logging.info("Analyzing layout...")
        try:
            layout = analyze_layout(detected_cards)
        except Exception as e:
            logging.error("analyze_layout() exception: %s", e)
            time.sleep(2)
            continue

        # 4️⃣ Create or update GameState
        if game_state is None:
            game_state = GameState(layout, card_positions=card_positions)
        else:
            # Update waste and tableau/foundation
            game_state.update_waste(layout.get("waste", []))
            game_state.tableau = layout.get("tableau", game_state.tableau)
            foundation_layout = layout.get("foundation", {})
            for suit in ["h", "c", "d", "s"]:
                game_state.foundation[suit] = foundation_layout.get(suit, game_state.foundation[suit])
            game_state.card_positions.update(card_positions)

        game_state.print_state()

        # 5️⃣ Generate and execute moves
        while True:
            logging.info("Generating valid moves...")
            try:
                mg = MoveGenerator(game_state)
                moves = mg.get_moves()
            except Exception as e:
                logging.error("MoveGenerator exception: %s", e)
                break

            if not moves:
                # No moves from visible cards: click stock to flip next card
                logging.info("No valid moves, clicking stock...")
                execute_move({"type": "stock_to_waste"}, game_state)
                time.sleep(0.5)
                break  # Capture fresh screenshot

            # Execute the first valid move
            best_move = moves[0]
            logging.info("Executing move: %s", best_move)
            execute_move(best_move, game_state)
            time.sleep(0.5)

        logging.info("Cycle complete. Waiting 2 seconds before next screenshot...")
        time.sleep(2)


def main():
    while True:
        try:
            os.system('cls' if os.name == 'nt' else 'clear')

            # Reload modules for live debugging
            for m in [
                "capture.screen_capture",
                "vision.detect_cards",
                "vision.card_layout",
                "logic.game_state",
                "logic.move_generator",
                "automation.move_executor",
            ]:
                try:
                    importlib.reload(importlib.import_module(m))
                except Exception:
                    pass

            run_game_loop()

        except Exception as e:
            logging.error("%s", e)
            time.sleep(2)


if __name__ == "__main__":
    main()
