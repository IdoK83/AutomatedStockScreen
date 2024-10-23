import streamlit as st
import pandas as pd
import re
import logging

# Set up logging for Streamlit (optional)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Clean percentage values
def clean_percentage(value):
    try:
        cleaned_value = re.sub(r'[^\d.-]', '', str(value))
        return float(cleaned_value)
    except ValueError:
        logging.error(f"Error cleaning percentage value: {value}")
        return None


# Process stock data
def process_stock_data(df):
    required_columns = [
        'Company Name', 'Ticker', 'Market Cap (mil)', 'Sector', 'Industry',
        'Exchange', 'Month of Fiscal Yr End', 'F0 Consensus Est.',
        'F1 Consensus Est.', 'F2 Consensus Est.', 'Annual Sales ($mil)',
        'F(1) Consensus Sales Est. ($mil)', 'SG-F1', 'EG-F1', 'EG-F2'
    ]

    if not all(column in df.columns for column in required_columns):
        st.error(f"Input CSV file must contain the following columns: {', '.join(required_columns)}")
        return None, None, None, None, None

    # Filter exchanges
    df = df[df['Exchange'].isin(['NSDQ', 'NYSE'])]

    # Clean numeric columns
    numeric_columns = ['SG-F1', 'EG-F1', 'EG-F2']
    for column in numeric_columns:
        df[column] = df[column].apply(lambda x: clean_percentage(x) if pd.notnull(x) else None)

    df = df.dropna(subset=numeric_columns)

    # Filter based on outlier conditions
    df_99 = df[(df['EG-F1'] == 99) | (df['SG-F1'] == 99) | (df['EG-F2'] == 99)]
    df_neg99 = df[(df['EG-F1'] == -99) | (df['SG-F1'] == -99) | (df['EG-F2'] == -99)]
    df_neg100 = df[(df['EG-F1'] == -100) | (df['SG-F1'] == -100) | (df['EG-F2'] == -100)]

    df_filtered = df[~df.index.isin(df_99.index) & ~df.index.isin(df_neg99.index) & ~df.index.isin(df_neg100.index)]

    # Calculate z-scores
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

    sector_averages = filtered_df.groupby('Sector')[numeric_columns].mean().reset_index()

    return filtered_df, df_99, df_neg99, df_neg100, sector_averages


# Streamlit app layout
st.title("Stock Data Processor")

uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Original Data", df)

    # Process the uploaded data
    filtered_df, df_99, df_neg99, df_neg100, sector_averages = process_stock_data(df)

    if filtered_df is not None:
        st.write("Filtered Data", filtered_df)
        st.write("Sector Averages", sector_averages)
        st.write("Stocks with EG-F1, SG-F1, or EG-F2 = 99", df_99)
        st.write("Stocks with EG-F1, SG-F1, or EG-F2 = -99", df_neg99)
        st.write("Stocks with EG-F1, SG-F1, or EG-F2 = -100", df_neg100)

        # Download options for each processed dataframe
        st.download_button(
            label="Download Filtered Data",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name='filtered_data.csv',
            mime='text/csv'
        )
        st.download_button(
            label="Download Sector Averages",
            data=sector_averages.to_csv(index=False).encode('utf-8'),
            file_name='sector_averages.csv',
            mime='text/csv'
        )
        st.download_button(
            label="Download Stocks with EG/SG = 99",
            data=df_99.to_csv(index=False).encode('utf-8'),
            file_name='stocks_99.csv',
            mime='text/csv'
        )
        st.download_button(
            label="Download Stocks with EG/SG = -99",
            data=df_neg99.to_csv(index=False).encode('utf-8'),
            file_name='stocks_neg99.csv',
            mime='text/csv'
        )
        st.download_button(
            label="Download Stocks with EG/SG = -100",
            data=df_neg100.to_csv(index=False).encode('utf-8'),
            file_name='stocks_neg100.csv',
            mime='text/csv'
        )
