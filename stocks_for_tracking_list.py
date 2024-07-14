import pandas as pd


# Function to load data
def load_data(file_path):
    return pd.read_csv(file_path)


# Function to filter data by sector
def filter_by_sector(data, sector):
    return data[data['Sector'] == sector]


# Function to calculate weighted performance score
def calculate_weighted_score(row, weights):
    return (weights['SG'] * row['SG'] +
            weights['EGF1'] * row['EGF1'] +
            weights['EGF2'] * row['EGF2'])


# Function to analyze stocks
def analyze_stocks(data, sector, weights, top_n=5):
    sector_data = filter_by_sector(data, sector)
    sector_data['WeightedScore'] = sector_data.apply(calculate_weighted_score, axis=1, weights=weights)
    top_performers = sector_data.sort_values(by='WeightedScore', ascending=False).head(top_n)
    return top_performers


# Main function
def main():
    file_path = 'stocks_data.csv'  # Path to the CSV file containing stock data
    over_performing_sector = 'Technology'  # Example sector
    weights = {'SG': 0.4, 'EGF1': 0.3, 'EGF2': 0.3}  # Example weights for the indices

    data = load_data(file_path)
    top_stocks = analyze_stocks(data, over_performing_sector, weights)

    print("Top Performing Stocks in the Over-Performing Sector:")
    print(top_stocks)


if __name__ == "__main__":
    main()