import streamlit as st
import pandas as pd
from growth_estimates import calculate_growth_metrics, filter_stocks, apply_z_score_filter, calculate_sector_averages
from momentum_score import calculate_momentum_score, apply_z_score_filter_momentum, calculate_sector_momentum_averages
from sector_analysis import score_sector_stocks
from utils import validate_columns

# Configuration
RELEVANT_EXCHANGES = ['NSDQ', 'NYSE']  # Only allow these exchanges

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
    2. Select either Growth Estimates Analysis or Momentum Analysis.
    3. Configure settings and generate sector analysis based on your chosen method.
    4. Download all outputs as needed.

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

    # Filter by relevant exchanges before processing
    df = df[df['Exchange'].isin(RELEVANT_EXCHANGES)]
    if df.empty:
        st.error("No stocks from the relevant exchanges found.")
        st.stop()

    # Analysis selection: Growth Estimates or Momentum
    analysis_type = st.radio("Choose Analysis Type", ["Growth Estimates Analysis", "Momentum Analysis"])

    if analysis_type == "Growth Estimates Analysis":
        # Process growth metrics
        df_growth = calculate_growth_metrics(df.copy())
        all_valid_stocks, flagged_stocks = filter_stocks(df_growth)
        valid_stocks_for_averages = apply_z_score_filter(all_valid_stocks)
        sector_growth_averages = calculate_sector_averages(valid_stocks_for_averages)

        # Display sector growth averages, formatted as percentages for growth metrics
        st.write("Sector Growth Averages (Excluding Outliers and Flags)", sector_growth_averages.style.format({
            'SG-F1': "{:.2%}", 'EG-F1': "{:.2%}", 'EG-F2': "{:.2%}"
        }))

        # Download options for growth analysis results
        st.write("Valid Stocks", all_valid_stocks)
        st.write("Flagged Stocks (99, -99 values)", flagged_stocks)
        st.download_button("Download Valid Stocks CSV", all_valid_stocks.to_csv(index=False), "valid_stocks.csv")
        st.download_button("Download Flagged Stocks CSV", flagged_stocks.to_csv(index=False), "flagged_stocks.csv")
        st.download_button("Download Sector Growth Averages CSV", sector_growth_averages.to_csv(index=False), "sector_growth_averages.csv")

        # Custom weight sliders for growth metrics
        st.subheader("Set Weights for Growth Metrics (Weighted Score Calculation)")
        weight_sg = st.slider("Weight for SG-F1", 0.0, 1.0, 0.5)
        weight_egf1 = st.slider("Weight for EG-F1", 0.0, 1.0, 0.3)
        weight_egf2 = st.slider("Weight for EG-F2", 0.0, 1.0, 0.2)
        growth_weights = {'SG': weight_sg, 'EGF1': weight_egf1, 'EGF2': weight_egf2}

        # Sector selection and scoring based on growth metrics
        selected_sector = st.selectbox("Choose a sector to analyze", sector_growth_averages['Sector'].unique())
        scored_stocks = score_sector_stocks(all_valid_stocks, selected_sector, weights=growth_weights, metric='WeightedScore', ascending=False)
        st.write("Scored Stocks by Growth Estimates", scored_stocks.style.format({
            'SG-F1': "{:.2%}", 'EG-F1': "{:.2%}", 'EG-F2': "{:.2%}", 'WeightedScore': "{:.2f}"
        }))
        st.download_button("Download Sector Analysis CSV", scored_stocks.to_csv(index=False), "scored_sector_stocks_growth.csv")

    elif analysis_type == "Momentum Analysis":
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

        # Create weights dictionary for momentum calculation
        momentum_weights = {
            '1 Week': weight_1_week,
            '4 Weeks': weight_4_weeks,
            '12 Weeks': weight_12_weeks,
            'YTD': weight_ytd
        }

        # Calculate and filter momentum scores
        df_momentum = calculate_momentum_score(df.copy(), weights=momentum_weights)
        valid_stocks_for_momentum = apply_z_score_filter_momentum(df_momentum)
        sector_momentum_averages = calculate_sector_momentum_averages(valid_stocks_for_momentum)

        # Sort and display sector momentum averages
        sector_momentum_averages = sector_momentum_averages.sort_values(by='MomentumScore', ascending=False)
        st.write("Sector Momentum Averages (Sorted by Momentum Score, Excluding Outliers)", sector_momentum_averages)
        st.download_button("Download Sector Momentum Averages CSV", sector_momentum_averages.to_csv(index=False), "sector_momentum_averages.csv")

        # Sector selection and scoring based on momentum scores
        selected_sector = st.selectbox("Choose a sector to analyze", sector_momentum_averages['Sector'].unique())
        scored_stocks = score_sector_stocks(valid_stocks_for_momentum, selected_sector, weights={}, metric='MomentumScore', ascending=False)
        st.write("Scored Stocks by Momentum Score", scored_stocks)
        st.download_button("Download Sector Analysis CSV", scored_stocks.to_csv(index=False), "scored_sector_stocks_momentum.csv")
