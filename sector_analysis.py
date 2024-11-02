import pandas as pd


def score_sector_stocks(df, sector, metric, ascending=False):
    """Scores stocks within the selected sector based on the chosen metric."""
    sector_data = df[df['Sector'] == sector]
    if len(sector_data) == 0:
        raise ValueError(f"No stocks found in the {sector} sector.")

    # Sort by the specified metric and assign ranks
    sector_data = sector_data.sort_values(metric, ascending=ascending)
    sector_data['Rank'] = range(1, len(sector_data) + 1)
    return sector_data
