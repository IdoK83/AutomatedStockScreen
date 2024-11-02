import streamlit as st
import pandas as pd
from growth_estimates import calculate_growth_metrics
from momentum_score import calculate_momentum_score
from sector_analysis import score_sector_stocks

# Required columns for validation
REQUIRED_COLUMNS = [
    'Company Name', 'Ticker', 'Market Cap (mil)', 'Sector', 'Industry', 'Exchange',
    'Month of Fiscal Yr End', 'F0 Consensus Est.', 'F1 Consensus Est.', 'F2 Consensus Est.',
    'Annual Sales ($mil)', 'F(1) Consensus Sales Est. ($mil)',
    '% Price Change (1 Week)', '% Price Change (4 Weeks)', '% Price Change (12 Weeks)', '% Price Change (YTD)'
]


def validate_columns(df):
    """Validates that the uploaded CSV contains all required columns."""
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        st.error(f"Missing columns in the uploaded CSV: {', '.join(missing_columns)}")
        return False
    return True


st.title("Stock Data Processor & Sector Analysis Tool")

uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Original Data", df)

    # Validate columns
    if not validate_columns(df):
        st.stop()  # Stop the app if columns are missing

    # Calculate growth estimates and momentum score independently
    df_growth = calculate_growth_metrics(df.copy())
    df_momentum = calculate_momentum_score(df.copy())

    # Filter out outliers for sector averages
    sector_growth_averages = df_growth.groupby('Sector')[['SG-F1', 'EG-F1', 'EG-F2']].mean()
    sector_momentum_averages = df_momentum.groupby('Sector')['MomentumScore'].mean().sort_values(ascending=False)

    # Display sector growth averages, formatted as percentages
    st.write("Sector Growth Averages (Excluding Outliers)", sector_growth_averages.style.format({
        'SG-F1': "{:.2%}", 'EG-F1': "{:.2%}", 'EG-F2': "{:.2%}"
    }))
    st.download_button("Download Sector Growth Averages CSV", sector_growth_averages.to_csv(),
                       "sector_growth_averages.csv", mime="text/csv")

    # Display sorted momentum averages
    st.write("Sector Momentum Averages (Excluding Outliers, Sorted by Momentum)", sector_momentum_averages)
    st.download_button("Download Sector Momentum Averages CSV", sector_momentum_averages.to_csv(),
                       "sector_momentum_averages.csv", mime="text/csv")

    # User chooses analysis type
    analysis_type = st.radio("Choose Analysis Type", ["Growth Estimates", "Momentum Score"])

    # Select sector for analysis
    selected_sector = st.selectbox("Choose a sector to analyze", sector_growth_averages.index)

    # Scoring logic based on user choice
    if analysis_type == "Growth Estimates":
        metric = st.selectbox("Choose Growth Metric", ['SG-F1', 'EG-F1', 'EG-F2'])
        scored_stocks = score_sector_stocks(df_growth, selected_sector, metric, ascending=False)
    else:
        scored_stocks = score_sector_stocks(df_momentum, selected_sector, 'MomentumScore', ascending=False)

    st.write("Scored Stocks", scored_stocks)
    st.download_button("Download Scored Stocks CSV", scored_stocks.to_csv(index=False), "scored_stocks.csv",
                       mime="text/csv")
