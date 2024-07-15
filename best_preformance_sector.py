import pandas as pd
import numpy as np
from scipy.stats import zscore
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def clean_percentage(value):
    try:
        cleaned_value = re.sub(r'[^\d.-]', '', str(value))
        return float(cleaned_value)
    except ValueError:
        logging.error(f"Error cleaning percentage value: {value}")
        return None


def process_stock_data(input_csv, filtered_stock_data_csv, output_99_csv, output_neg99_csv, output_neg100_csv, sector_averages_csv):
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        logging.error(f"File not found: {input_csv}")
        return
    except pd.errors.EmptyDataError:
        logging.error(f"File is empty: {input_csv}")
        return

    logging.info("Initial data loaded")
    logging.info(df.head())

    required_columns = [
        'Company Name', 'Ticker', 'Market Cap (mil)', 'Sector', 'Industry',
        'Exchange', 'Month of Fiscal Yr End', 'F0 Consensus Est.',
        'F1 Consensus Est.', 'F2 Consensus Est.', 'Annual Sales ($mil)',
        'F(1) Consensus Sales Est. ($mil)', 'SG-F1', 'EG-F1', 'EG-F2'
    ]

    if not all(column in df.columns for column in required_columns):
        raise ValueError(f"Input CSV file must contain the following columns: {', '.join(required_columns)}")

    df = df[df['Exchange'].isin(['NSDQ', 'NYSE'])]
    logging.info(f"After filtering by exchange, {len(df)} rows remain.")

    numeric_columns = ['SG-F1', 'EG-F1', 'EG-F2']
    for column in numeric_columns:
        df[column] = df[column].apply(lambda x: clean_percentage(x) if pd.notnull(x) else None)

    df = df.dropna(subset=numeric_columns)
    logging.info(f"After dropping rows with NaNs in {numeric_columns}, {len(df)} rows remain.")

    if len(df) == 0:
        logging.warning("No data remaining after dropping NaN values.")
        return

    df_99 = df[(df['EG-F1'] == 99) | (df['SG-F1'] == 99) | (df['EG-F2'] == 99)]
    df_neg99 = df[(df['EG-F1'] == -99) | (df['SG-F1'] == -99) | (df['EG-F2'] == -99)]
    df_neg100 = df[(df['EG-F1'] == -100) | (df['SG-F1'] == -100) | (df['EG-F2'] == -100)]

    df_filtered = df[~df.index.isin(df_99.index) & ~df.index.isin(df_neg99.index) & ~df.index.isin(df_neg100.index)]

    def calculate_robust_zscores(group):
        for column in numeric_columns:
            median = group[column].median()
            iqr = group[column].quantile(0.75) - group[column].quantile(0.25)
            group[f'{column}_zscore'] = (group[column] - median) / iqr
        return group

    df_grouped = df_filtered.groupby('Sector', as_index=False, group_keys=False).apply(calculate_robust_zscores)

    filtered_df = df_grouped[
        (df_grouped['SG-F1_zscore'].abs() <= 3) &
        (df_grouped['EG-F1_zscore'].abs() <= 3) &
        (df_grouped['EG-F2_zscore'].abs() <= 3)
    ]
    logging.info(f"After filtering outliers, {len(filtered_df)} rows remain.")

    if len(filtered_df) == 0:
        logging.warning("No data remaining after filtering outliers.")
        return

    sector_averages = filtered_df.groupby('Sector')[numeric_columns].mean().reset_index()

    try:
        filtered_df.to_csv(filtered_stock_data_csv, index=False)
        df_99.to_csv(output_99_csv, index=False)
        df_neg99.to_csv(output_neg99_csv, index=False)
        df_neg100.to_csv(output_neg100_csv, index=False)
        sector_averages.to_csv(sector_averages_csv, index=False)
    except Exception as e:
        logging.error(f"Error writing to CSV files: {e}")
        return

    return sector_averages


def apply_coloring(df):
    def color_cells(val, avg, min_val):
        if val > avg:
            return 'background-color: green'
        elif val == min_val:
            return 'background-color: red'
        return ''

    avg_values = df.mean(numeric_only=True)
    min_values = df.min(numeric_only=True)

    styled_df = df.style.applymap(lambda x: color_cells(x, avg_values['SG-F1'], min_values['SG-F1']), subset=['SG-F1'])
    styled_df = styled_df.applymap(lambda x: color_cells(x, avg_values['EG-F1'], min_values['EG-F1']), subset=['EG-F1'])
    styled_df = styled_df.applymap(lambda x: color_cells(x, avg_values['EG-F2'], min_values['EG-F2']), subset=['EG-F2'])

    return styled_df


def main():
    input_csv = r"C:\Users\keina\python_stock_screener\SECTOR GROWTH ANALYSIS - EXAMPLE1.csv"
    filtered_stock_data_csv = r"C:\Users\keina\python_stock_screener\filtered_stock_data.csv"
    output_99_csv = r"C:\Users\keina\python_stock_screener\stocks_99.csv"
    output_neg99_csv = r"C:\Users\keina\python_stock_screener\stocks_neg99.csv"
    output_neg100_csv = r"C:\Users\keina\python_stock_screener\stocks_neg100.csv"
    sector_averages_csv = r"C:\Users\keina\python_stock_screener\sector_averages.csv"
    sector_averages_colored_excel = r"C:\Users\keina\python_stock_screener\sector_averages_colored.xlsx"

    sector_averages = process_stock_data(input_csv, filtered_stock_data_csv, output_99_csv, output_neg99_csv, output_neg100_csv, sector_averages_csv)

    if sector_averages is None:
        logging.error("Processing stock data failed.")
        return

    styled_averages = apply_coloring(sector_averages)
    styled_averages.to_excel(sector_averages_colored_excel, engine='openpyxl', index=False)
    logging.info(f"Sector averages with coloring saved to {sector_averages_colored_excel}")


if __name__ == "__main__":
    main()
