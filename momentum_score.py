import pandas as pd

MOMENTUM_COLUMNS = [
    '% Price Change (1 Week)',
    '% Price Change (4 Weeks)',
    '% Price Change (12 Weeks)',
    '% Price Change (YTD)'
]

def calculate_momentum_score(df, weights=None):
    """Calculates a momentum score based on price changes across multiple periods."""
    if weights is None:
        weights = {'1 Week': 0.25, '4 Weeks': 0.25, '12 Weeks': 0.25, 'YTD': 0.25}  # Default equal weights

    # Calculate z-scores for each period's price change
    for period in MOMENTUM_COLUMNS:
        df[f'{period}_zscore'] = (df[period] - df[period].mean()) / df[period].std()

    # Calculate weighted sum for momentum score
    df['MomentumScore'] = (
        weights['1 Week'] * df['% Price Change (1 Week)_zscore'] +
        weights['4 Weeks'] * df['% Price Change (4 Weeks)_zscore'] +
        weights['12 Weeks'] * df['% Price Change (12 Weeks)_zscore'] +
        weights['YTD'] * df['% Price Change (YTD)_zscore']
    )

    # Drop z-score columns for a clean output
    df = df.drop(columns=[f'{period}_zscore' for period in MOMENTUM_COLUMNS])
    return df
