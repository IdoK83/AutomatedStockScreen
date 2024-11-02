import pandas as pd

MOMENTUM_COLUMNS = [
    '% Price Change (1 Week)',
    '% Price Change (4 Weeks)',
    '% Price Change (12 Weeks)',
    '% Price Change (YTD)'
]

def calculate_momentum_score(df, weights=None):
    """Calculates a momentum score based on a weighted average of percentage changes across multiple periods."""
    if weights is None:
        weights = {'1 Week': 0.25, '4 Weeks': 0.25, '12 Weeks': 0.25, 'YTD': 0.25}  # Default equal weights

    # Calculate weighted momentum score directly from percentage changes
    df['MomentumScore'] = (
        weights['1 Week'] * df['% Price Change (1 Week)'] +
        weights['4 Weeks'] * df['% Price Change (4 Weeks)'] +
        weights['12 Weeks'] * df['% Price Change (12 Weeks)'] +
        weights['YTD'] * df['% Price Change (YTD)']
    )
    return df
