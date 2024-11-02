def calculate_weighted_score(row, weights):
    """Calculates a weighted score for a stock."""
    return (weights['SG'] * row['SG-F1'] +
            weights['EGF1'] * row['EG-F1'] +
            weights['EGF2'] * row['EG-F2'])


def score_sector_stocks(df, sector, weights=None, metric='WeightedScore', ascending=False):
    """Scores stocks within the selected sector based on a chosen metric."""
    sector_data = df[df['Sector'] == sector]
    if len(sector_data) == 0:
        raise ValueError(f"No stocks found in the {sector} sector.")

    # Calculate weighted score if growth metrics are selected
    if metric == 'WeightedScore' and weights:
        sector_data[metric] = sector_data.apply(calculate_weighted_score, axis=1, weights=weights)

    # Sort by the chosen metric (WeightedScore or MomentumScore)
    sector_data = sector_data.sort_values(metric, ascending=ascending)
    sector_data['Rank'] = range(1, len(sector_data) + 1)

    return sector_data