def decimal_to_probability(decimal_odds):
    '''
    Converts decimal odds to implied probability of winning.
    
    Decimal odds represent the total return for each $1 bet (including the original stake).
    The implied probability is simply the inverse of the decimal odds.
    
    Formula: probability = 1 / decimal_odds

    Parameters:
        decimal_odds (float): The decimal odds value (must be > 1)

    Returns:
        float: The implied probability as a percentage, rounded to 2 decimal places
    '''
    if decimal_odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    return round((1 / decimal_odds) * 100, 2)


def american_to_probability(american_odds):
    '''
    Converts American (moneyline) odds to implied probability of winning.

    American odds can be:
      - Positive (e.g. +150): indicates how much profit you'd make on a $100 bet
      - Negative (e.g. -200): indicates how much you'd need to bet to win $100 profit

    The formula differs based on whether the odds are positive or negative:
        If positive: probability = 100 / (odds + 100)
        If negative: probability = -odds / (-odds + 100)

    Parameters:
        american_odds (int): The American odds value (can be positive or negative)

    Returns:
        float: The implied probability as a percentage, rounded to 2 decimal places
    '''
    if american_odds > 0:
        probability = 100 / (american_odds + 100)
    else:
        probability = -american_odds / (-american_odds + 100)
    return round(probability * 100, 2)

def round_to_nearest_2_digits(x):
    """
    Rounds a number to the nearest value with two significant digits.

    For example:
    - 356200 becomes 360000
    - 724 becomes 720
    - 0 remains 0

    Args:
        x (int or float): The number to round.

    Returns:
        int: The rounded number.
    """
    from math import log10, floor
    if x == 0:
        return 0
    digits = int(floor(log10(abs(x))))
    return round(x, -digits + 1)

