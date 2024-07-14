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

    def calculate_sector_zscores(group):
        for column in numeric_columns:
            group[f'{column}_zscore'] = zscore(group[column])
        return group

    df_grouped = df_filtered.groupby('Sector', as_index=False).apply(calculate_sector_zscores)

    filtered_df = df_grouped[
        (df_grouped['SG-F1_zscore'].abs() <= 3) &
        (df_grouped['EG-F1_zscore'].abs() <= 3) &
        (df_grouped['EG-F2_zscore'].abs() <= 3)
    ]
    logging.info(f"After filtering outliers, {len(filtered_df)} rows remain.")

    if len(filtered_df) == 0:
        logging.warning("No data remaining after filtering outliers.")
        return

    sector_averages = filtered_df.groupby('Sector')[numeric_columns].mean()

    try:
        filtered_df.to_csv(filtered_stock_data_csv, index=False)
        df_99.to_csv(output_99_csv, index=False)
        df_neg99.to_csv(output_neg99_csv, index=False)
        df_neg100.to_csv(output_neg100_csv, index=False)
        sector_averages.to_csv(sector_averages_csv)
    except Exception as e:
        logging.error(f"Error writing to CSV files: {e}")
        return

    return filtered_df


def calculate_weighted_score(row, weights):
    return (weights['SG'] * row['SG-F1'] +
            weights['EGF1'] * row['EG-F1'] +
            weights['EGF2'] * row['EG-F2'])


def find_top_stocks(filtered_df, sector, weights, z_threshold=1.2, top_percentage=0.1, ascending=False):
    sector_data = filtered_df[filtered_df['Sector'] == sector]
    sector_data = sector_data[
        (sector_data['SG-F1_zscore'].abs() <= z_threshold) &
        (sector_data['EG-F1_zscore'].abs() <= z_threshold) &
        (sector_data['EG-F2_zscore'].abs() <= z_threshold)
    ]

    if len(sector_data) == 0:
        logging.warning(f"No stocks in the {sector} sector meet the z-score threshold.")
        return pd.DataFrame()

    sector_data['WeightedScore'] = sector_data.apply(calculate_weighted_score, axis=1, weights=weights)

    top_n = int(len(sector_data) * top_percentage)
    top_stocks = sector_data.nlargest(top_n, 'WeightedScore') if not ascending else sector_data.nsmallest(top_n, 'WeightedScore')
    return top_stocks


def main():
    input_csv = r"C:\Users\keina\python_stock_screener\SECTOR GROWTH ANALYSIS - EXAMPLE1.csv"
    filtered_stock_data_csv = r"C:\Users\keina\python_stock_screener\filtered_stock_data.csv"
    output_99_csv = r"C:\Users\keina\python_stock_screener\stocks_99.csv"
    output_neg99_csv = r"C:\Users\keina\python_stock_screener\stocks_neg99.csv"
    output_neg100_csv = r"C:\Users\keina\python_stock_screener\stocks_neg100.csv"
    sector_averages_csv = r"C:\Users\keina\python_stock_screener\sector_averages.csv"
    top_stocks_output_csv = r"C:\Users\keina\python_stock_screener\top_10_percent_stocks.csv"

    filtered_df = process_stock_data(input_csv, filtered_stock_data_csv, output_99_csv, output_neg99_csv, output_neg100_csv, sector_averages_csv)

    if filtered_df is None:
        logging.error("Processing stock data failed.")
        return

    sector_averages = filtered_df.groupby('Sector')['F1 Consensus Est.'].mean()

    n_top_sectors = 3
    n_bottom_sectors = 2
    top_percentage = 0.1
    weights = {'SG': 0.4, 'EGF1': 0.3, 'EGF2': 0.3}
    z_threshold = 1.2

    top_sectors = sector_averages.nlargest(n_top_sectors).index.tolist()
    bottom_sectors = sector_averages.nsmallest(n_bottom_sectors).index.tolist()

    all_top_stocks = []
    all_bottom_stocks = []

    for sector in top_sectors:
        logging.info(f"\nAnalyzing top sector: {sector}")
        top_stocks = find_top_stocks(filtered_df, sector, weights, z_threshold, top_percentage, ascending=False)
        top_stocks['Sector'] = sector
        top_stocks['Type'] = 'Long'
        all_top_stocks.append(top_stocks)

    for sector in bottom_sectors:
        logging.info(f"\nAnalyzing bottom sector: {sector}")
        bottom_stocks = find_top_stocks(filtered_df, sector, weights, z_threshold, top_percentage, ascending=True)
        bottom_stocks['Sector'] = sector
        bottom_stocks['Type'] = 'Short'
        all_bottom_stocks.append(bottom_stocks)

    final_top_stocks = pd.concat(all_top_stocks)
    final_bottom_stocks = pd.concat(all_bottom_stocks)
    final_stocks = pd.concat([final_top_stocks, final_bottom_stocks])

    if final_stocks.empty:
        logging.warning("No top or bottom stocks found.")
        return

    try:
        final_stocks.to_csv(top_stocks_output_csv, index=False)
        logging.info(f"Top and bottom performing stocks saved to {top_stocks_output_csv}")
    except Exception as e:
        logging.error(f"Error writing to {top_stocks_output_csv}: {e}")


if __name__ == "__main__":
    main()
