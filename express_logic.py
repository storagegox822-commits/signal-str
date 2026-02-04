import itertools

class ExpressGenerator:
    def __init__(self):
        self.outcomes_3way = ["Win", "Draw", "Loss"]  # 1X2
        self.outcomes_2way = ["Under", "Over"]      # Totals
        self.outcomes_oe = ["Odd", "Even"]          # Odd/Even

    def generate_27_system(self, matches):
        """
        Generates 27 combinations for 3 matches with 3 outcomes each.
        Matches: list of strings ["Team A vs B", "Team C vs D", "Team E vs F"]
        Returns: List of bets (each bet is a list of 3 selection strings)
        """
        if len(matches) != 3:
            return []
        
        # Cross product of 3 matches x 3 outcomes
        # Outcome list depends on market. Assuming 3-way (1x2) for the classic "27 express" system
        # or it could be Correct Score groups etc. 
        # Standard 27 system usually refers to covering all outcomes of 3 matches in a 3-way market.
        
        combinations = list(itertools.product(self.outcomes_3way, repeat=3))
        
        system_bets = []
        for combo in combinations:
            bet_slip = []
            for i, outcome in enumerate(combo):
                bet_slip.append(f"{matches[i]} - {outcome}")
            system_bets.append(bet_slip)
            
        return system_bets

    def generate_binary_system(self, matches, mode="Under/Over"):
        """
        Generates 8 combinations for 3 matches with 2 outcomes (2^3 = 8)
        """
        if len(matches) != 3:
            return []
            
        outcomes = self.outcomes_2way if mode == "Under/Over" else self.outcomes_oe
        combinations = list(itertools.product(outcomes, repeat=3))
        
        system_bets = []
        for combo in combinations:
            bet_slip = []
            for i, outcome in enumerate(combo):
                bet_slip.append(f"{matches[i]} - {outcome}")
            system_bets.append(bet_slip)
            
        return system_bets

    def swap_odd_even(self, current_selection):
        """
        Swaps "Odd" to "Even" and vice versa. Useful for hedging.
        Input: "Team A vs B - Odd"
        """
        if " - Odd" in current_selection:
            return current_selection.replace(" - Odd", " - Even")
        elif " - Even" in current_selection:
            return current_selection.replace(" - Even", " - Odd")
        return current_selection
