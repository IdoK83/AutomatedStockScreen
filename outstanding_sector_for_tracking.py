import streamlit as st
import pandas as pd
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
RELEVANT_EXCHANGES = ['NSDQ', 'NYSE']
NUMERIC_COLUMNS = ['SG-F1', 'EG-F1', 'EG-F2']


# Function to display instructions for the user
def display_instructions():
    st.subheader("Instructions for Use")

    st.markdown("""
    ### Welcome to the Stock Data Processor & Sector Analysis Tool!

    This application processes stock data by calculating growth metrics, filtering outliers, and analyzing specific sectors based on user-defined criteria.

    **Features:**
    - **Growth Metrics Calculation**: Computes `SG-F1`, `EG-F1`, and `EG-F2` to evaluate sales and earnings growth.
    - **Flagged Value Filtering**: Excludes stocks with flagged values (`99`, `-99`).
    - **Outlier Removal**: Removes extreme outliers using z-scores, retaining only stocks within a 3-sigma range for sector averages.
    - **Weighted Scoring**: Allows users to score stocks within a selected sector using custom weights and strategies (Long/Short).
    - **Downloadable Reports**: Provides filtered datasets, sector averages, and scored sector analysis as CSV files.

    **Required Columns:**
    The app expects a CSV file with the following columns:
    - `Company Name`: The name of the company.
    - `Ticker`: The stock ticker symbol.
    - `Market Cap (mil)`: The market capitalization in millions.
    - `Sector`: The sector to which the company belongs.
    - `Industry`: The industry to which the company belongs.
    - `Exchange`: The stock exchange (e.g., NSDQ, NYSE).
    - `Month of Fiscal Yr End`: The month the fiscal year ends.
    - `F0 Consensus Est.`: Consensus estimate for fiscal year 0 (F0).
    - `F1 Consensus Est.`: Consensus estimate for fiscal year 1 (F1).
    - `F2 Consensus Est.`: Consensus estimate for fiscal year 2 (F2).
    - `Annual Sales ($mil)`: Annual sales in millions of dollars.
    - `F(1) Consensus Sales Est. ($mil)`: Consensus sales estimate for fiscal year 1.

    **Filtering Process:**
    - **Flagged Values** (`99` and `-99`) are excluded to ensure data accuracy.
    - **Outlier Detection**: Uses z-scores to remove stocks with extreme values, filtering out any with absolute z-scores above 3.
    - **Sector Averages**: Calculated only from filtered stocks, excluding flagged and extreme outliers.

    **How to Use the App:**
    1. Upload a CSV file with the required columns.
    2. Review filtered data, flagged stocks, and sector averages.
    3. Select a sector and analysis type (Long/Short), then set custom weights for growth metrics.
    4. Generate scored sector data and download all outputs as needed.

    ### Source Code:
    Access the full source code for this project on GitHub:
    [AutomatedStockScreen GitHub Repository](https://github.com/IdoK83/AutomatedStockScreen)
    """)


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


def filter_by_exchange(df):
    """Filters out stocks that are not from the required exchanges."""
    return df[df['Exchange'].isin(RELEVANT_EXCHANGES)]


def filter_stocks(df):
    """Separates valid stocks and flagged stocks (99 and -99) for independent analysis."""
    # Filter out flagged stocks
    valid_stocks = df[~df[NUMERIC_COLUMNS].isin([99, -99]).any(axis=1)]
    flagged_stocks = df[df[NUMERIC_COLUMNS].isin([99, -99]).any(axis=1)]

    return valid_stocks, flagged_stocks


def apply_z_score_filter(df):
    """Filters out extreme outliers based on z-scores for valid stocks."""
    for column in NUMERIC_COLUMNS:
        median = df[column].median()
        iqr = df[column].quantile(0.75) - df[column].quantile(0.25)
        df[f'{column}_zscore'] = (df[column] - median) / iqr

    # Filter out rows where z-score is greater than 3 in absolute value
    filtered_df = df[
        (df['SG-F1_zscore'].abs() <= 3) &
        (df['EG-F1_zscore'].abs() <= 3) &
        (df['EG-F2_zscore'].abs() <= 3)
        ]

    # Drop z-score columns for a clean final output
    return filtered_df.drop(columns=[f'{col}_zscore' for col in NUMERIC_COLUMNS])


def calculate_sector_averages(valid_stocks):
    """Calculates sector averages from valid stocks, excluding flagged values and outliers."""
    return valid_stocks.groupby('Sector')[NUMERIC_COLUMNS].mean().reset_index()


# Weighted Scoring Function
def calculate_weighted_score(row, weights):
    """Calculates a weighted score for a stock."""
    return (weights['SG'] * row['SG-F1'] +
            weights['EGF1'] * row['EG-F1'] +
            weights['EGF2'] * row['EG-F2'])


def score_sector_stocks(filtered_df, sector, weights, ascending=False):
    """Scores stocks within the selected sector based on the weighted score."""
    sector_data = filtered_df[filtered_df['Sector'] == sector]
    if len(sector_data) == 0:
        st.warning(f"No stocks found in the {sector} sector.")
        return pd.DataFrame()

    sector_data['WeightedScore'] = sector_data.apply(calculate_weighted_score, axis=1, weights=weights)
    sector_data = sector_data.sort_values('WeightedScore', ascending=ascending)
    sector_data['Rank'] = range(1, len(sector_data) + 1)

    return sector_data


# Main processing function
def process_stock_data(df):
    df = filter_by_exchange(df)  # Only keep stocks from required exchanges
    df = calculate_growth_metrics(df)
    if df is None:
        return None, None, None

    # Separate valid and flagged stocks
    valid_stocks, flagged_stocks = filter_stocks(df)
    valid_stocks = apply_z_score_filter(valid_stocks)  # Apply z-score filtering to remove outliers
    sector_averages = calculate_sector_averages(
        valid_stocks)  # Calculate sector averages based on z-score filtered stocks
    return valid_stocks, flagged_stocks, sector_averages


# Streamlit app layout
st.title("Stock Data Processor & Sector Analysis Tool")

# Display the instructions at the top of the page
display_instructions()

uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Original Data", df)

    # Process and display data
    valid_stocks, flagged_stocks, sector_averages = process_stock_data(df)

    if valid_stocks is not None:
        # Display and download the sector averages and filtered stocks
        st.write("Sector Averages (Excluding Outliers and Flags)", sector_averages.style.format({
            'SG-F1': "{:.2%}", 'EG-F1': "{:.2%}", 'EG-F2': "{:.2%}"
        }))
        st.write("Valid Stocks", valid_stocks)
        st.write("Flagged Stocks (99, -99 values)", flagged_stocks)

        # Download buttons for CSV outputs
        st.download_button("Download Valid Stocks CSV", valid_stocks.to_csv(index=False), "valid_stocks.csv",
                           mime="text/csv")
        st.download_button("Download Flagged Stocks CSV", flagged_stocks.to_csv(index=False), "flagged_stocks.csv",
                           mime="text/csv")
        st.download_button("Download Sector Averages CSV", sector_averages.to_csv(index=False), "sector_averages.csv",
                           mime="text/csv")

        # Explanation and sector selection for scoring
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
            scored_stocks = score_sector_stocks(valid_stocks, selected_sector, weights, ascending)
            if not scored_stocks.empty:
                st.write("Scored Stocks", scored_stocks.style.format({
                    'SG-F1': "{:.2%}", 'EG-F1': "{:.2%}", 'EG-F2': "{:.2%}", 'WeightedScore': "{:.2f}"
                }))
                st.download_button("Download Sector Analysis CSV", scored_stocks.to_csv(index=False),
                                   "scored_sector_stocks.csv", mime="text/csv")
            else:
                st.write("No stocks met the analysis criteria.")
