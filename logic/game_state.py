# logic/game_state.py
class GameState:
    def __init__(self, layout, card_positions=None):
        """
        layout: dict from analyze_layout()
            Keys:
                waste: list of card names
                foundation: dict or list of cards
                tableau: dict 1..7 -> list of cards
        card_positions: dict {card_name: (x, y)} for GUI execution
        """
        # Stock placeholder (always empty, click stock to cycle)
        self.stock = []

        # Waste
        self.waste = list(layout.get("waste", []))

        # Foundation
        self.foundation = {'h': [], 'c': [], 'd': [], 's': []}
        foundation_layout = layout.get("foundation", {})

        if isinstance(foundation_layout, list):
            # Convert list to dict by suit
            for card in foundation_layout:
                if card:
                    suit = card[-1].lower()
                    self.foundation[suit].append(card)
        elif isinstance(foundation_layout, dict):
            for suit in ['h', 'c', 'd', 's']:
                self.foundation[suit] = list(foundation_layout.get(suit, []))

        # Tableau
        self.tableau = {i: list(layout.get("tableau", {}).get(i, [])) for i in range(1, 8)}

        # Card positions
        self.card_positions = card_positions if card_positions else {}
        self._assign_missing_positions()

    # ---------------- Internal helpers ----------------
    def _assign_missing_positions(self):
        """Fill missing positions for tableau, waste, and foundation."""
        # Tableau
        x_centers = [355, 605, 783, 959, 1135, 1310, 1490]
        TABLEAU_Y_OFFSET = 40
        for col_idx, col_cards in self.tableau.items():
            for depth, card in enumerate(col_cards):
                if card not in self.card_positions:
                    x = x_centers[col_idx-1]
                    y = 310 + depth * TABLEAU_Y_OFFSET
                    self.card_positions[card] = (x, y)

        # Waste
        for idx, card in enumerate(self.waste):
            if card not in self.card_positions:
                x = 536 + idx * 100
                y = 310
                self.card_positions[card] = (x, y)

        # Foundation
        suit_centers = {'h': 960, 'c': 1135, 'd': 1310, 's': 1490}
        for suit, pile in self.foundation.items():
            for card in pile:
                if card not in self.card_positions:
                    self.card_positions[card] = (suit_centers[suit], 200)

    # ---------------- Public methods ----------------
    def update_waste(self, detected_waste):
        """Sync internal waste with newly detected waste cards."""
        # Add new waste cards
        for card in detected_waste:
            if card not in self.waste:
                self.waste.append(card)
        # Remove cards that disappeared from waste (already moved to foundation/tableau)
        self.waste = [c for c in self.waste if c in detected_waste]

    def move_to_foundation(self, card_name):
        """Move a card to its foundation pile and remove from tableau/waste."""
        suit = card_name[-1].lower()
        if suit not in self.foundation:
            return
        if card_name not in self.foundation[suit]:
            self.foundation[suit].append(card_name)

        if card_name in self.waste:
            self.waste.remove(card_name)
        for col in self.tableau.values():
            if card_name in col:
                col.remove(card_name)

    def move_tableau_to_tableau(self, sequence, from_col, to_col):
        """Move sequence of cards from one tableau column to another."""
        for c in sequence:
            if c in self.tableau[from_col]:
                self.tableau[from_col].remove(c)
            self.tableau[to_col].append(c)

    def print_state(self):
        print("\n--- GAME STATE ---")
        print("Stock (clickable placeholder):", self.stock)
        print("Waste:", self.waste)
        print("Foundation:", self.foundation)
        print("Tableau:")
        for i in range(1, 8):
            print(f"  Column {i}: {self.tableau.get(i, [])}")
        print("Card Positions:")
        for card, pos in self.card_positions.items():
            print(f"  {card}: {pos}")
