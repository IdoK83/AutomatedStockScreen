import streamlit as st
import pandas as pd
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Clean percentage values
def clean_percentage_column(column):
    def try_parse_float(value):
        try:
            # Remove any non-numeric characters, handle scientific notation
            cleaned_value = re.sub(r'[^\d.eE+-]', '', str(value))  # Allow digits, '.' and scientific notation 'e' or 'E'
            return float(cleaned_value)
        except ValueError:
            # Log or handle any conversion errors and return None for invalid entries
            logging.warning(f"Could not convert value to float: {value}")
            return None

    # Apply the try_parse_float function to each element in the column
    return column.apply(try_parse_float)

# Calculate SG-F1, EG-F1, and EG-F2 based on the provided formulas
def calculate_new_columns(df):
    # Find the necessary columns dynamically by their names
    try:
        annual_sales_col = df.columns[df.columns.str.contains('Annual Sales', case=False, regex=False)][0]
        f1_sales_est_col = df.columns[df.columns.str.contains('F\(1\) Consensus Sales Est', case=False, regex=True)][0]
        f0_est_col = df.columns[df.columns.str.contains('F0 Consensus Est', case=False, regex=False)][0]
        f1_est_col = df.columns[df.columns.str.contains('F1 Consensus Est', case=False, regex=False)][0]
        f2_est_col = df.columns[df.columns.str.contains('F2 Consensus Est', case=False, regex=False)][0]

        # Filter out rows with missing or zero values necessary for the calculations
        df = df.dropna(subset=[f1_sales_est_col, annual_sales_col, f0_est_col, f1_est_col, f2_est_col])
        df = df[(df[f0_est_col] != 0) & (df[f1_est_col] != 0) & (df[annual_sales_col] != 0)]

        # Apply the formulas for SG-F1, EG-F1, EG-F2
        df['SG-F1'] = df[f1_sales_est_col] / df[annual_sales_col] - 1

        df['EG-F1'] = df.apply(
            lambda row: 99 if row[f0_est_col] < 0 and row[f1_est_col] > 0 else (
                -99 if row[f0_est_col] < 0 and row[f1_est_col] <= 0 else (
                    -99 if row[f0_est_col] > 0 and row[f1_est_col] < 0 else row[f1_est_col] / row[f0_est_col] - 1)),
            axis=1)

        df['EG-F2'] = df.apply(
            lambda row: 99 if row[f1_est_col] < 0 and row[f2_est_col] > 0 else (
                -99 if row[f1_est_col] < 0 and row[f2_est_col] <= 0 else (
                    -99 if row[f1_est_col] > 0 and row[f2_est_col] < 0 else row[f2_est_col] / row[f1_est_col] - 1)),
            axis=1)

    except KeyError as e:
        st.error(f"Missing necessary columns to calculate SG-F1, EG-F1, and EG-F2: {str(e)}")
        return None

    return df


# Process stock data
def process_stock_data(df):
    required_columns = [
        'Company Name', 'Ticker', 'Market Cap (mil)', 'Sector', 'Industry',
        'Exchange', 'Month of Fiscal Yr End', 'F0 Consensus Est.',
        'F1 Consensus Est.', 'F2 Consensus Est.', 'Annual Sales ($mil)',
        'F(1) Consensus Sales Est. ($mil)'
    ]

    # Check if all required columns are present
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        st.error(f"Missing columns in input file: {', '.join(missing_columns)}")
        return None, None, None, None, None, None

    # Filter for relevant exchanges
    df = df[df['Exchange'].isin(['NSDQ', 'NYSE'])]

    # Clean numeric columns
    df = calculate_new_columns(df)
    if df is None:
        return None, None, None, None, None, None

    numeric_columns = ['SG-F1', 'EG-F1', 'EG-F2']
    df[numeric_columns] = df[numeric_columns].apply(clean_percentage_column)

    df = df.dropna(subset=numeric_columns)

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
        # Display formatted as percentage without multiplying by 100
        st.write("Filtered Data", filtered_df.style.format({
            'SG-F1': "{:.2%}",  # Format as percentage without changing the value
            'EG-F1': "{:.2%}",
            'EG-F2': "{:.2%}"
        }))
        st.write("Sector Averages", sector_averages.style.format({
            'SG-F1': "{:.2%}",
            'EG-F1': "{:.2%}",
            'EG-F2': "{:.2%}"
        }))
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
