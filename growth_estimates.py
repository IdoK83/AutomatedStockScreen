import pandas as pd

NUMERIC_COLUMNS = ['SG-F1', 'EG-F1', 'EG-F2']

def calculate_growth_metrics(df):
    """Calculates SG-F1, EG-F1, and EG-F2 growth metrics."""
    try:
        annual_sales_col = df.columns[df.columns.str.contains('Annual Sales', case=False, regex=False)][0]
        f1_sales_est_col = df.columns[df.columns.str.contains('F\\(1\\) Consensus Sales Est', case=False, regex=True)][0]
        f0_est_col = df.columns[df.columns.str.contains('F0 Consensus Est', case=False, regex=False)][0]
        f1_est_col = df.columns[df.columns.str.contains('F1 Consensus Est', case=False, regex=False)][0]
        f2_est_col = df.columns[df.columns.str.contains('F2 Consensus Est', case=False, regex=False)][0]

        # Drop rows with missing or zero values in essential columns
        df = df.dropna(subset=[f1_sales_est_col, annual_sales_col, f0_est_col, f1_est_col, f2_est_col])
        df = df[(df[f0_est_col] != 0) & (df[f1_est_col] != 0) & (df[annual_sales_col] != 0)]

        # Calculations
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
