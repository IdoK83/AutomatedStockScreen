import streamlit as st
import pandas as pd
from growth_estimates import calculate_growth_metrics
from momentum_score import calculate_momentum_score
from sector_analysis import score_sector_stocks

st.title("Stock Data Processor & Sector Analysis Tool")

uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Original Data", df)

    # Calculate growth estimates and momentum score independently
    df_growth = calculate_growth_metrics(df.copy())
    df_momentum = calculate_momentum_score(df.copy())

    # Filter out outliers for sector averages
    sector_growth_averages = df_growth.groupby('Sector')[['SG-F1', 'EG-F1', 'EG-F2']].mean()
    sector_momentum_averages = df_momentum.groupby('Sector')['MomentumScore'].mean()

    # Display sector averages
    st.write("Sector Growth Averages (Excluding Outliers)", sector_growth_averages)
    st.write("Sector Momentum Averages (Excluding Outliers)", sector_momentum_averages)

    # User chooses analysis type
    analysis_type = st.radio("Choose Analysis Type", ["Growth Estimates", "Momentum Score"])

    # Select sector for analysis
    selected_sector = st.selectbox("Choose a sector to analyze", sector_growth_averages.index)

    if analysis_type == "Growth Estimates":
        metric = st.selectbox("Choose Growth Metric", ['SG-F1', 'EG-F1', 'EG-F2'])
        scored_stocks = score_sector_stocks(df_growth, selected_sector, metric, ascending=False)
    else:
        scored_stocks = score_sector_stocks(df_momentum, selected_sector, 'MomentumScore', ascending=False)

    st.write("Scored Stocks", scored_stocks)
    st.download_button("Download Scored Stocks CSV", scored_stocks.to_csv(index=False), "scored_stocks.csv",
                       mime="text/csv")
