import streamlit as st
import pandas as pd
from growth_estimates import calculate_growth_metrics, filter_stocks, apply_z_score_filter, calculate_sector_averages
from momentum_score import calculate_momentum_score, apply_z_score_filter_momentum, calculate_sector_momentum_averages
from sector_analysis import score_sector_stocks
from utils import validate_columns

def display_instructions():
    st.subheader("Instructions for Use")

    st.markdown("""
    ### Welcome to the Stock Data Processor & Sector Analysis Tool!

    This application processes stock data by calculating growth metrics, filtering outliers, and analyzing specific sectors based on user-defined criteria.

    **Features:**
    - **Growth Metrics Calculation**: Computes `SG-F1`, `EG-F1`, and `EG-F2` to evaluate sales and earnings growth.
    - **Momentum Score Calculation**: Computes a weighted momentum score based on price changes over various periods.
    - **Flagged Value Filtering**: Excludes stocks with flagged values (`99`, `-99`).
    - **Outlier Removal**: Removes extreme outliers using z-scores, retaining only stocks within a 3-sigma range for sector averages.
    - **Weighted Scoring**: Allows users to score stocks within a selected sector using custom weights and strategies (Long/Short).
    - **Downloadable Reports**: Provides filtered datasets, sector averages, and scored sector analysis as CSV files.

    **Required Columns:**
    The app expects a CSV file with the following columns:
    - `Company Name`, `Ticker`, `Market Cap (mil)`, `Sector`, `Industry`, `Exchange`,
      `Month of Fiscal Yr End`, `F0 Consensus Est.`, `F1 Consensus Est.`, `F2 Consensus Est.`, 
      `Annual Sales ($mil)`, `F(1) Consensus Sales Est. ($mil)`, `% Price Change (1 Week)`, 
      `% Price Change (4 Weeks)`, `% Price Change (12 Weeks)`, `% Price Change (YTD)`

    **How to Use the App:**
    1. Upload a CSV file with the required columns.
    2. Review filtered data, flagged stocks, and sector averages.
    3. Select a sector and analysis type (Growth or Momentum), then set custom weights if needed.
    4. Generate scored sector data and download all outputs as needed.

    ### Source Code:
    Access the full source code for this project on GitHub:
    [AutomatedStockScreen GitHub Repository](https://github.com/IdoK83/AutomatedStockScreen)
    """)


st.title("Stock Data Processor & Sector Analysis Tool")
display_instructions()

# Upload CSV file
uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Original Data", df)

    # Validate columns
    try:
        validate_columns(df)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # Calculate growth metrics and momentum score independently
    df_growth = calculate_growth_metrics(df.copy())

    # Custom weight sliders for momentum score calculation
    st.subheader("Set Custom Weights for Momentum Score Calculation")
    weight_1_week = st.slider("Weight for 1 Week Change", 0.0, 1.0, 0.25)
    weight_4_weeks = st.slider("Weight for 4 Weeks Change", 0.0, 1.0, 0.25)
    weight_12_weeks = st.slider("Weight for 12 Weeks Change", 0.0, 1.0, 0.25)
    weight_ytd = st.slider("Weight for YTD Change", 0.0, 1.0, 0.25)

    # Normalize weights to ensure they sum to 1
    total_weight = weight_1_week + weight_4_weeks + weight_12_weeks + weight_ytd
    if total_weight != 1.0:
        weight_1_week, weight_4_weeks, weight_12_weeks, weight_ytd = (
            weight_1_week / total_weight, weight_4_weeks / total_weight,
            weight_12_weeks / total_weight, weight_ytd / total_weight
        )

    # Create weights dictionary to pass to calculate_momentum_score
    momentum_weights = {
        '1 Week': weight_1_week,
        '4 Weeks': weight_4_weeks,
        '12 Weeks': weight_12_weeks,
        'YTD': weight_ytd
    }

    # Calculate momentum score with user-defined weights
    df_momentum = calculate_momentum_score(df.copy(), weights=momentum_weights)

    # Filter out outliers for momentum scores and calculate sector momentum averages
    valid_stocks_for_momentum = apply_z_score_filter_momentum(df_momentum)
    sector_momentum_averages = calculate_sector_momentum_averages(valid_stocks_for_momentum)

    # Display and allow download of sector momentum averages
    st.write("Sector Momentum Averages (Excluding Outliers)", sector_momentum_averages)
    st.download_button("Download Sector Momentum Averages CSV", sector_momentum_averages.to_csv(index=False),
                       "sector_momentum_averages.csv")

    # Sector analysis options for momentum
    selected_sector = st.selectbox("Choose a sector to analyze", sector_momentum_averages['Sector'].unique())
    scored_stocks = score_sector_stocks(valid_stocks_for_momentum, selected_sector, weights={}, metric='MomentumScore',
                                        ascending=False)

    # Display and download scored stocks for the selected sector
    st.write("Scored Stocks by Momentum Score", scored_stocks)
    st.download_button("Download Sector Analysis CSV", scored_stocks.to_csv(index=False), "scored_sector_stocks.csv")