REQUIRED_COLUMNS = [
    'Company Name', 'Ticker', 'Market Cap (mil)', 'Sector', 'Industry', 'Exchange',
     'F0 Consensus Est.', 'F1 Consensus Est.', 'F2 Consensus Est.',
    'Annual Sales ($mil)', 'F(1) Consensus Sales Est. ($mil)'
]

def validate_columns(df):
    """Validates that the uploaded CSV contains all required columns."""
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns in the uploaded CSV: {', '.join(missing_columns)}")
    return True


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

