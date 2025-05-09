from math import log10, floor
from typing import Union

class DataFormatter:
    """Helper class for formatting and converting between different odds formats."""
    
    @staticmethod
    def decimal_to_probability(decimal_odds: float) -> float:
        """
        Converts decimal odds to implied probability of winning.
        
        Decimal odds represent the total return for each $1 bet (including the original stake).
        The implied probability is simply the inverse of the decimal odds.
        
        Formula: probability = 1 / decimal_odds

        Args:
            decimal_odds: The decimal odds value (must be > 1)

        Returns:
            The implied probability as a percentage, rounded to 2 decimal places
            
        Raises:
            ValueError: If decimal_odds is less than or equal to 1
        """
        if decimal_odds <= 1:
            raise ValueError("Decimal odds must be greater than 1")
        return round((1 / decimal_odds) * 100, 2)

    @staticmethod
    def american_to_probability(american_odds: int) -> float:
        """
        Converts American (moneyline) odds to implied probability of winning.

        American odds can be:
          - Positive (e.g. +150): indicates how much profit you'd make on a $100 bet
          - Negative (e.g. -200): indicates how much you'd need to bet to win $100 profit

        The formula differs based on whether the odds are positive or negative:
            If positive: probability = 100 / (odds + 100)
            If negative: probability = -odds / (-odds + 100)

        Args:
            american_odds: The American odds value (can be positive or negative)

        Returns:
            The implied probability as a percentage, rounded to 2 decimal places
        """
        if american_odds > 0:
            probability = 100 / (american_odds + 100)
        else:
            probability = -american_odds / (-american_odds + 100)
        return round(probability * 100, 2)

    @staticmethod
    def round_to_significant_digits(x: Union[int, float], digits: int = 2) -> int:
        """
        Rounds a number to the nearest value with specified significant digits.

        For example, with 2 significant digits:
        - 356200 becomes 360000
        - 724 becomes 720
        - 0 remains 0

        Args:
            x: The number to round
            digits: Number of significant digits (default: 2)

        Returns:
            The rounded number
        """
        if x == 0:
            return 0
        magnitude = int(floor(log10(abs(x))))
        return round(x, -magnitude + digits - 1)

    @staticmethod
    def decimal_to_american(decimal_odds: float) -> int:
        """
        Converts decimal odds to American (moneyline) odds.

        Args:
            decimal_odds: The decimal odds value (must be > 1)

        Returns:
            The American odds value

        Raises:
            ValueError: If decimal_odds is less than or equal to 1
        """
        if decimal_odds <= 1:
            raise ValueError("Decimal odds must be greater than 1")
        
        if decimal_odds >= 2:
            return int(round((decimal_odds - 1) * 100))
        else:
            return int(round(-100 / (decimal_odds - 1)))

    @staticmethod
    def american_to_decimal(american_odds: int) -> float:
        """
        Converts American (moneyline) odds to decimal odds.

        Args:
            american_odds: The American odds value (can be positive or negative)

        Returns:
            The decimal odds value
        """
        if american_odds > 0:
            return round(american_odds / 100 + 1, 3)
        else:
            return round(100 / abs(american_odds) + 1, 3) 