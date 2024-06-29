import pandas as pd
import numpy as np
from scipy.stats import zscore
import re


def clean_percentage(value):
    try:
        # Remove any non-numeric characters (e.g., %, $)
        cleaned_value = re.sub(r'[^\d.-]', '', str(value))
        return float(cleaned_value)
    except ValueError:
        return None


def process_stock_data(input_csv, output_csv, output_99_csv, output_neg99_csv):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(input_csv)
    print("Initial data loaded:")
    print(df.head())

    # Ensure necessary columns are present
    required_columns = [
        'Company Name', 'Ticker', 'Market Cap (mil)', 'Sector', 'Industry',
        'Exchange', 'Month of Fiscal Yr End', 'F0 Consensus Est.',
        'F1 Consensus Est.', 'F2 Consensus Est.', 'Annual Sales ($mil)',
        'F(1) Consensus Sales Est. ($mil)', 'SG-F1', 'EG-F1', 'EG-F2'
    ]

    if not all(column in df.columns for column in required_columns):
        raise ValueError(f"Input CSV file must contain the following columns: {', '.join(required_columns)}")

    # Filter by exchange (only NSDQ and NYSE)
    df = df[df['Exchange'].isin(['NSDQ', 'NYSE'])]
    print(f"After filtering by exchange, {len(df)} rows remain.")

    # Clean percentage strings and convert to numeric
    numeric_columns = ['SG-F1', 'EG-F1', 'EG-F2']
    for column in numeric_columns:
        df[column] = df[column].apply(lambda x: clean_percentage(x) if pd.notnull(x) else None)

    # Drop rows with any NaN values in the necessary columns
    df = df.dropna(subset=numeric_columns)
    print(f"After dropping rows with NaNs in {numeric_columns}, {len(df)} rows remain.")

    if len(df) == 0:
        print("No data remaining after dropping NaN values.")
        return

    # Filter out 99% and -99% rows into separate DataFrames
    df_99 = df[(df['EG-F1'] == 99) | (df['SG-F1'] == 99) | (df['EG-F2'] == 99)]
    df_neg99 = df[(df['EG-F1'] == -99) | (df['SG-F1'] == -99) | (df['EG-F2'] == -99)]

    # Remove the 99% and -99% rows from the original DataFrame
    df_filtered = df[~df.index.isin(df_99.index) & ~df.index.isin(df_neg99.index)]

    # Calculate sector-specific Z-scores and filter outliers
    def calculate_sector_zscores(group):
        for column in numeric_columns:
            group[f'{column}_zscore'] = zscore(group[column])
        return group

    df_grouped = df_filtered.groupby('Sector', as_index=False).apply(calculate_sector_zscores)

    # Filter out rows where any of the sector-specific Z-scores are greater than 3
    filtered_df = df_grouped[
        (df_grouped['SG-F1_zscore'].abs() <= 3) &
        (df_grouped['EG-F1_zscore'].abs() <= 3) &
        (df_grouped['EG-F2_zscore'].abs() <= 3)
    ]
    print(f"After filtering outliers, {len(filtered_df)} rows remain.")

    if len(filtered_df) == 0:
        print("No data remaining after filtering outliers.")
        return

    # Compute average values by sector only for numeric columns
    sector_averages = filtered_df.groupby('Sector')[numeric_columns].mean()

    # Count of stocks per sector that passed filters
    sector_stock_count = filtered_df.groupby('Sector')['Ticker'].count()
    sector_averages['Stocks Count'] = sector_stock_count  # Add count to sector_averages DataFrame

    # Save the results to CSV files
    sector_averages.to_csv(output_csv)
    df_99.to_csv(output_99_csv)
    df_neg99.to_csv(output_neg99_csv)

    print(f"Averages by sector saved to {output_csv}")
    print(f"Stocks with 99% values saved to {output_99_csv}")
    print(f"Stocks with -99% values saved to {output_neg99_csv}")
    print(sector_averages)

# Example usage
input_csv = r"C:\Users\keina\python_stock_screener\SECTOR GROWTH ANALYSIS - EXAMPLE1.csv"  # Replace with your input CSV file path
output_csv = r"C:\Users\keina\python_stock_screener\sector_averages.csv"  # Replace with your desired output CSV file path
output_99_csv = r"C:\Users\keina\python_stock_screener\stocks_99.csv"  # Replace with your desired output CSV file path for 99% values
output_neg99_csv = r"C:\Users\keina\python_stock_screener\stocks_neg99.csv"  # Replace with your desired output CSV file path for -99% values

process_stock_data(input_csv, output_csv, output_99_csv, output_neg99_csv)
