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
