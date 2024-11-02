import pandas as pd

NUMERIC_COLUMNS = ['SG-F1', 'EG-F1', 'EG-F2']

def calculate_growth_metrics(df):
    """Calculates SG-F1, EG-F1, and EG-F2 growth metrics."""
    try:
        # Identify required columns by pattern matching
        annual_sales_col = df.columns[df.columns.str.contains('Annual Sales', case=False, regex=False)][0]
        f1_sales_est_col = df.columns[df.columns.str.contains('F\\(1\\) Consensus Sales Est', case=False, regex=True)][0]
        f0_est_col = df.columns[df.columns.str.contains('F0 Consensus Est', case=False, regex=False)][0]
        f1_est_col = df.columns[df.columns.str.contains('F1 Consensus Est', case=False, regex=False)][0]
        f2_est_col = df.columns[df.columns.str.contains('F2 Consensus Est', case=False, regex=False)][0]

        # Drop rows with missing or zero values in essential columns
        df = df.dropna(subset=[f1_sales_est_col, annual_sales_col, f0_est_col, f1_est_col, f2_est_col])
        df = df[(df[f0_est_col] != 0) & (df[f1_est_col] != 0) & (df[annual_sales_col] != 0)]

        # Calculate SG-F1, EG-F1, and EG-F2
        df['SG-F1'] = df[f1_sales_est_col] / df[annual_sales_col] - 1
        df['EG-F1'] = df.apply(lambda row: calc_growth(row[f0_est_col], row[f1_est_col]), axis=1)
        df['EG-F2'] = df.apply(lambda row: calc_growth(row[f1_est_col], row[f2_est_col]), axis=1)

    except KeyError as e:
        raise ValueError(f"Missing necessary columns to calculate growth metrics: {str(e)}")
    return df

def calc_growth(fiscal0, fiscal1):
    """Calculates growth between two fiscal estimates with handling for flags."""
    if fiscal0 < 0 and fiscal1 > 0:
        return 99
    elif fiscal0 < 0 and fiscal1 <= 0:
        return -99
    elif fiscal0 > 0 and fiscal1 < 0:
        return -99
    else:
        return fiscal1 / fiscal0 - 1

def filter_stocks(df):
    """Separates valid stocks and flagged stocks (99 and -99) for independent analysis."""
    valid_stocks = df[~df[NUMERIC_COLUMNS].isin([99, -99]).any(axis=1)]
    flagged_stocks = df[df[NUMERIC_COLUMNS].isin([99, -99]).any(axis=1)]
    return valid_stocks, flagged_stocks

def apply_z_score_filter(df):
    """Filters out extreme outliers based on z-scores for valid stocks."""
    for column in NUMERIC_COLUMNS:
        median = df[column].median()
        iqr = df[column].quantile(0.75) - df[column].quantile(0.25)
        df[f'{column}_zscore'] = (df[column] - median) / iqr

    filtered_df = df[
        (df['SG-F1_zscore'].abs() <= 3) & (df['EG-F1_zscore'].abs() <= 3) & (df['EG-F2_zscore'].abs() <= 3)
    ]
    return filtered_df.drop(columns=[f'{col}_zscore' for col in NUMERIC_COLUMNS])

def calculate_sector_averages(valid_stocks):
    """Calculates sector averages from valid stocks, excluding flagged values and outliers."""
    return valid_stocks.groupby('Sector')[NUMERIC_COLUMNS].mean().reset_index()
