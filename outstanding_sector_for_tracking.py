import streamlit as st
import pandas as pd
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
RELEVANT_EXCHANGES = ['NSDQ', 'NYSE']
NUMERIC_COLUMNS = ['SG-F1', 'EG-F1', 'EG-F2']


# Utility Functions
def clean_percentage_column(column):
    """Cleans a numeric column by converting values to floats and handling scientific notation."""

    def try_parse_float(value):
        try:
            cleaned_value = re.sub(r'[^\d.eE+-]', '', str(value))
            return float(cleaned_value)
        except ValueError:
            logging.warning(f"Could not convert value to float: {value}")
            return None

    return column.apply(try_parse_float)


def calculate_growth_metrics(df):
    """Calculates SG-F1, EG-F1, and EG-F2 growth metrics."""
    try:
        annual_sales_col = df.columns[df.columns.str.contains('Annual Sales', case=False, regex=False)][0]
        f1_sales_est_col = df.columns[df.columns.str.contains('F\\(1\\) Consensus Sales Est', case=False, regex=True)][
            0]
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
        st.error(f"Missing necessary columns to calculate growth metrics: {str(e)}")
        return None
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


def filter_outliers_and_flagged(df):
    """Filters out flagged values and outliers based on z-scores."""
    # Remove flagged values (99 and -99)
    df = df[~df[NUMERIC_COLUMNS].isin([99, -99]).any(axis=1)]

    # Calculate z-scores for each numeric column
    for column in NUMERIC_COLUMNS:
        median = df[column].median()
        iqr = df[column].quantile(0.75) - df[column].quantile(0.25)
        df[f'{column}_zscore'] = (df[column] - median) / iqr

    # Filter out rows where z-score > 3
    filtered_df = df[
        (df['SG-F1_zscore'].abs() <= 3) &
        (df['EG-F1_zscore'].abs() <= 3) &
        (df['EG-F2_zscore'].abs() <= 3)
        ]

    # Drop z-score columns for a clean final output
    return filtered_df.drop(columns=[f'{col}_zscore' for col in NUMERIC_COLUMNS])


def filter_stocks(df):
    """Filters out irrelevant exchanges and cleans numeric columns."""
    df = df[df['Exchange'].isin(RELEVANT_EXCHANGES)]
    df[NUMERIC_COLUMNS] = df[NUMERIC_COLUMNS].apply(clean_percentage_column)
    df = df.dropna(subset=NUMERIC_COLUMNS)
    return df


def calculate_sector_averages(valid_stocks):
    """Calculates sector averages from valid stocks, excluding flagged values and outliers."""
    return valid_stocks.groupby('Sector')[NUMERIC_COLUMNS].mean().reset_index()


# Main processing function
def process_stock_data(df):
    df = calculate_growth_metrics(df)
    if df is None:
        return None, None

    df = filter_stocks(df)
    df_filtered = filter_outliers_and_flagged(df)  # Filter out flagged values and outliers
    sector_averages = calculate_sector_averages(df_filtered)  # Calculate sector averages on filtered data
    return df_filtered, sector_averages


# Streamlit UI Components
st.title("Stock Data Processor & Sector Analysis Tool")

uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Original Data", df)

    # Process and display data
    all_valid_stocks, sector_averages = process_stock_data(df)

    if all_valid_stocks is not None:
        st.write("Sector Averages (Excluding Outliers)", sector_averages.style.format({
            'SG-F1': "{:.2%}", 'EG-F1': "{:.2%}", 'EG-F2': "{:.2%}"
        }))

        # Explanation and sector selection
        st.markdown("""
        ### Sector Analysis
        - Based on the calculated sector averages, identify a sector you'd like to analyze.
        - Choose an analysis type: **Long** (to focus on top-scoring stocks) or **Short** (to focus on bottom-scoring stocks).
        - Set custom weights for each growth metric (SG-F1, EG-F1, EG-F2) to define their impact on the overall weighted score.
        """)

        selected_sector = st.selectbox("Choose a sector to analyze", sector_averages['Sector'].unique())
        analysis_type = st.radio("Analysis Type", ["Long", "Short"])

        # User-defined weights for weighted scoring
        st.markdown("#### Set Weights for Weighted Score Calculation")
        weight_sg = st.slider("Weight for SG-F1 (Sales Growth)", 0.0, 1.0, 0.5)
        weight_egf1 = st.slider("Weight for EG-F1 (Earnings Growth F1)", 0.0, 1.0, 0.3)
        weight_egf2 = st.slider("Weight for EG-F2 (Earnings Growth F2)", 0.0, 1.0, 0.2)

        # Normalize weights if needed (ensure they sum up to 1)
        total_weight = weight_sg + weight_egf1 + weight_egf2
        if total_weight != 1.0:
            weight_sg, weight_egf1, weight_egf2 = weight_sg / total_weight, weight_egf1 / total_weight, weight_egf2 / total_weight

        weights = {'SG': weight_sg, 'EGF1': weight_egf1, 'EGF2': weight_egf2}
        ascending = True if analysis_type == 'Short' else False

        if st.button("Analyze Sector"):
            scored_stocks = score_sector_stocks(all_valid_stocks, selected_sector, weights, ascending)
            if not scored_stocks.empty:
                st.write("Scored Stocks", scored_stocks.style.format({
                    'SG-F1': "{:.2%}", 'EG-F1': "{:.2%}", 'EG-F2': "{:.2%}", 'WeightedScore': "{:.2f}"
                }))
                st.download_button("Download Sector Analysis CSV", scored_stocks.to_csv(index=False),
                                   "scored_sector_stocks.csv", mime="text/csv")
            else:
                st.write("No stocks met the analysis criteria.")
