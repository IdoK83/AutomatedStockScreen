import streamlit as st
import pandas as pd
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Clean percentage values
def clean_percentage_column(column):
    return column.astype(str).str.replace(r'[^\d.-]', '', regex=True).astype(float)

# Process stock data
def process_stock_data(df):
    required_columns = [
        'Company Name', 'Ticker', 'Market Cap (mil)', 'Sector', 'Industry',
        'Exchange', 'Month of Fiscal Yr End', 'F0 Consensus Est.',
        'F1 Consensus Est.', 'F2 Consensus Est.', 'Annual Sales ($mil)',
        'F(1) Consensus Sales Est. ($mil)', 'SG-F1', 'EG-F1', 'EG-F2'
    ]

    # Check if all required columns are present
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        st.error(f"Missing columns in input file: {', '.join(missing_columns)}")
        return None, None, None, None, None, None

    # Filter for relevant exchanges
    df = df[df['Exchange'].isin(['NSDQ', 'NYSE'])]

    # Clean numeric columns
    numeric_columns = ['SG-F1', 'EG-F1', 'EG-F2']
    df[numeric_columns] = df[numeric_columns].apply(clean_percentage_column)

    df = df.dropna(subset=numeric_columns)

    # Helper function to filter outliers
    def filter_outliers(value):
        if value in [99, -99, -100]:
            return value
        return None

    # Filter rows with outliers
    df_99 = df[df[numeric_columns].isin([99]).any(axis=1)]
    df_neg99 = df[df[numeric_columns].isin([-99]).any(axis=1)]
    df_neg100 = df[df[numeric_columns].isin([-100]).any(axis=1)]

    df_filtered = df[~df.index.isin(df_99.index) & ~df.index.isin(df_neg99.index) & ~df.index.isin(df_neg100.index)]

    # Calculate z-scores
    def calculate_robust_zscores(group):
        for column in numeric_columns:
            median = group[column].median()
            iqr = group[column].quantile(0.75) - group[column].quantile(0.25)
            group[f'{column}_zscore'] = (group[column] - median) / iqr
        return group

    df_grouped = df_filtered.groupby('Sector', as_index=False, group_keys=False).apply(calculate_robust_zscores)

    # Extract extreme z-score stocks
    df_extreme = df_grouped[
        (df_grouped['SG-F1_zscore'].abs() > 3) |
        (df_grouped['EG-F1_zscore'].abs() > 3) |
        (df_grouped['EG-F2_zscore'].abs() > 3)
    ]

    # Filtered dataframe excluding extreme stocks
    filtered_df = df_grouped[
        (df_grouped['SG-F1_zscore'].abs() <= 3) &
        (df_grouped['EG-F1_zscore'].abs() <= 3) &
        (df_grouped['EG-F2_zscore'].abs() <= 3)
    ]

    sector_averages = filtered_df.groupby('Sector')[numeric_columns].mean().reset_index()

    return filtered_df, df_99, df_neg99, df_neg100, sector_averages, df_extreme

# Streamlit app layout
st.title("Stock Data Processor")

uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Original Data", df)

    # Process the uploaded data
    filtered_df, df_99, df_neg99, df_neg100, sector_averages, df_extreme = process_stock_data(df)

    if filtered_df is not None:
        st.write("Filtered Data", filtered_df)
        st.write("Sector Averages", sector_averages)
        st.write("Stocks with EG-F1, SG-F1, or EG-F2 = 99", df_99)
        st.write("Stocks with EG-F1, SG-F1, or EG-F2 = -99", df_neg99)
        st.write("Stocks with EG-F1, SG-F1, or EG-F2 = -100", df_neg100)
        st.write("Extreme Z-Score Stocks", df_extreme)

        # Download options
        def download_button(label, dataframe, file_name):
            st.download_button(
                label=label,
                data=dataframe.to_csv(index=False).encode('utf-8'),
                file_name=file_name,
                mime='text/csv'
            )

        download_button("Download Filtered Data", filtered_df, 'filtered_data.csv')
        download_button("Download Sector Averages", sector_averages, 'sector_averages.csv')
        download_button("Download Stocks with EG/SG = 99", df_99, 'stocks_99.csv')
        download_button("Download Stocks with EG/SG = -99", df_neg99, 'stocks_neg99.csv')
        download_button("Download Stocks with EG/SG = -100", df_neg100, 'stocks_neg100.csv')
        download_button("Download Extreme Z-Score Stocks", df_extreme, 'extreme_valued_stocks.csv')
