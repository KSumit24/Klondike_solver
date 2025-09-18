# logic/move_generator.py

RANK_VALUES = {
    'a': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    '7': 7, '8': 8, '9': 9, '10': 10, 'j': 11, 'q': 12, 'k': 13
}

COLOR = {'h': 'red', 'd': 'red', 'c': 'black', 's': 'black'}


class MoveGenerator:
    def __init__(self, game_state):
        self.game_state = game_state
        self.moves = []
        self._generate_moves()
        # Sort moves by priority: foundation > tableau > stock
        self.moves.sort(key=lambda m: self._move_priority(m))

    # ----------------- Internal helpers -----------------
    def _rank_value(self, card_name):
        return RANK_VALUES.get(card_name[:-1].lower(), 0)

    def _card_color(self, card_name):
        return COLOR.get(card_name[-1].lower())

    def _top_tableau_card(self, col):
        col_cards = self.game_state.tableau.get(col, [])
        return col_cards[-1] if col_cards else None

    def _can_move_to_foundation(self, card_name):
        suit = card_name[-1].lower()
        foundation_pile = self.game_state.foundation.get(suit, [])
        rank = self._rank_value(card_name)
        if not foundation_pile and rank == 1:  # Ace
            return True
        if foundation_pile:
            top_rank = self._rank_value(foundation_pile[-1])
            return rank == top_rank + 1
        return False

    def _can_place_on_tableau(self, moving_card, target_card):
        if not target_card:
            return self._rank_value(moving_card) == 13  # King on empty
        return (
            self._rank_value(moving_card) + 1 == self._rank_value(target_card) and
            self._card_color(moving_card) != self._card_color(target_card)
        )

    def _move_priority(self, move):
        t = move.get("type", "")
        if "foundation" in t:
            return 0
        elif "tableau" in t:
            return 1
        elif "stock" in t:
            return 2
        return 10

    # ----------------- Move generation -----------------
    def _generate_moves(self):
        self.moves = []
        self._waste_to_foundation()
        self._tableau_to_foundation()
        self._waste_to_tableau()
        self._tableau_to_tableau()
        self._stock_to_waste()

    def _waste_to_foundation(self):
        if not self.game_state.waste:
            return
        top_card = self.game_state.waste[-1]
        if self._can_move_to_foundation(top_card):
            self.moves.append({
                "type": "waste_to_foundation",
                "card": top_card
            })

    def _tableau_to_foundation(self):
        for col, cards in self.game_state.tableau.items():
            if not cards:
                continue
            top_card = cards[-1]
            if self._can_move_to_foundation(top_card):
                self.moves.append({
                    "type": "tableau_to_foundation",
                    "card": top_card,
                    "from_column": col
                })

    def _waste_to_tableau(self):
        if not self.game_state.waste:
            return
        top_card = self.game_state.waste[-1]
        for col in range(1, 8):
            target_card = self._top_tableau_card(col)
            if self._can_place_on_tableau(top_card, target_card):
                self.moves.append({
                    "type": "waste_to_tableau",
                    "card": top_card,
                    "to_column": col
                })

    def _tableau_to_tableau(self):
        for from_col in range(1, 8):
            from_cards = self.game_state.tableau.get(from_col, [])
            if not from_cards:
                continue
            for i in range(len(from_cards)):
                sequence = from_cards[i:]
                moving_card = sequence[0]
                for to_col in range(1, 8):
                    if to_col == from_col:
                        continue
                    target_card = self._top_tableau_card(to_col)
                    if self._can_place_on_tableau(moving_card, target_card):
                        self.moves.append({
                            "type": "tableau_to_tableau",
                            "sequence": sequence,
                            "card": moving_card,
                            "from_column": from_col,
                            "to_column": to_col
                        })

    def _stock_to_waste(self):
        if self.game_state.stock:
            self.moves.append({"type": "stock_to_waste"})

    # ----------------- Public -----------------
    def get_moves(self):
        return self.moves
