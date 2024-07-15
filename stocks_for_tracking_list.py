import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def calculate_weighted_score(row, weights):
    return (weights['SG'] * row['SG-F1'] +
            weights['EGF1'] * row['EG-F1'] +
            weights['EGF2'] * row['EG-F2'])


def find_top_stocks(filtered_df, sector, weights, z_threshold, top_percentage, ascending=False):
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
    filtered_stock_data_csv = r"C:\Users\keina\python_stock_screener\filtered_stock_data.csv"
    sector_averages_csv = r"C:\Users\keina\python_stock_screener\sector_averages.csv"
    output_csv = r"C:\Users\keina\python_stock_screener\top_stocks_at_xyz_sector.csv"

    filtered_df = pd.read_csv(filtered_stock_data_csv)
    sector_averages = pd.read_csv(sector_averages_csv)

    print("Available sectors and the number of stocks:")
    print(filtered_df['Sector'].value_counts())

    sector = input("Enter the sector you want to analyze: ")
    z_threshold = float(input("Enter the z-score threshold: "))
    top_percentage = float(input("Enter the top percentage (in decimal form, e.g., 0.1 for 10%): "))
    analysis_type = input("Enter 'long' for top-performing stocks or 'short' for worst-performing stocks: ").strip().lower()

    weights = {'SG': 0.4, 'EGF1': 0.3, 'EGF2': 0.3}
    ascending = True if analysis_type == 'short' else False

    top_stocks = find_top_stocks(filtered_df, sector, weights, z_threshold, top_percentage, ascending)

    if top_stocks.empty:
        logging.warning("No stocks found based on the criteria.")
        return

    top_stocks['Type'] = 'Short' if ascending else 'Long'
    top_stocks.to_csv(output_csv, index=False)
    logging.info(f"Stocks analysis result saved to {output_csv}")


if __name__ == "__main__":
    main()
