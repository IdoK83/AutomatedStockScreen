import streamlit as st
import pandas as pd
from growth_estimates import calculate_growth_metrics, filter_stocks, apply_z_score_filter, calculate_sector_averages
from momentum_score import calculate_momentum_score, apply_z_score_filter_momentum, calculate_sector_momentum_averages
from sector_analysis import score_sector_stocks
from utils import validate_columns

st.title("Stock Data Processor & Sector Analysis Tool")
display_instructions()

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
    df_momentum = calculate_momentum_score(df.copy())

    # Separate valid and flagged stocks for growth estimates
    all_valid_stocks, flagged_stocks = filter_stocks(df_growth)
    valid_stocks_for_averages = apply_z_score_filter(all_valid_stocks)
    sector_growth_averages = calculate_sector_averages(valid_stocks_for_averages)

    # Filter out outliers for momentum scores and calculate sector momentum averages
    valid_stocks_for_momentum = apply_z_score_filter_momentum(df_momentum)
    sector_momentum_averages = calculate_sector_momentum_averages(valid_stocks_for_momentum)

    # Display sector averages, formatted as percentages for growth metrics
    st.write("Sector Growth Averages (Excluding Outliers and Flags)", sector_growth_averages.style.format({
        'SG-F1': "{:.2%}", 'EG-F1': "{:.2%}", 'EG-F2': "{:.2%}"
    }))
    st.write("Sector Momentum Averages (Excluding Outliers)", sector_momentum_averages)

    # Display valid and flagged stocks
    st.write("Valid Stocks", all_valid_stocks)
    st.write("Flagged Stocks (99, -99 values)", flagged_stocks)

    # Download buttons for CSV outputs
    st.download_button("Download Valid Stocks CSV", all_valid_stocks.to_csv(index=False), "valid_stocks.csv")
    st.download_button("Download Flagged Stocks CSV", flagged_stocks.to_csv(index=False), "flagged_stocks.csv")
    st.download_button("Download Sector Growth Averages CSV", sector_growth_averages.to_csv(index=False),
                       "sector_growth_averages.csv")
    st.download_button("Download Sector Momentum Averages CSV", sector_momentum_averages.to_csv(index=False),
                       "sector_momentum_averages.csv")

    # Sector analysis
    selected_sector = st.selectbox("Choose a sector to analyze", sector_growth_averages['Sector'].unique())
    analysis_type = st.radio("Analysis Type", ["Growth Estimates", "Momentum Score"])

    if analysis_type == "Growth Estimates":
        # Custom weights for growth analysis
        st.markdown("#### Set Weights for Growth Metrics (Weighted Score Calculation)")
        weight_sg = st.slider("Weight for SG-F1", 0.0, 1.0, 0.5)
        weight_egf1 = st.slider("Weight for EG-F1", 0.0, 1.0, 0.3)
        weight_egf2 = st.slider("Weight for EG-F2", 0.0, 1.0, 0.2)
        weights = {'SG': weight_sg, 'EGF1': weight_egf1, 'EGF2': weight_egf2}
        # Score stocks by weighted growth metrics
        scored_stocks = score_sector_stocks(all_valid_stocks, selected_sector, weights, metric='WeightedScore',
                                            ascending=(analysis_type == "Short"))
        st.write("Scored Stocks by Growth Estimates",
                 scored_stocks.style.format({'SG-F1': "{:.2%}", 'EG-F1': "{:.2%}", 'EG-F2': "{:.2%}"}))
    else:
        # Score stocks by momentum score
        scored_stocks = score_sector_stocks(valid_stocks_for_momentum, selected_sector, weights={},
                                            metric='MomentumScore', ascending=False)
        st.write("Scored Stocks by Momentum Score", scored_stocks)

    # Download button for analyzed sector stocks
    st.download_button("Download Sector Analysis CSV", scored_stocks.to_csv(index=False), "scored_sector_stocks.csv")
