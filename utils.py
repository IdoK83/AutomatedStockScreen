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

def remove_spam_columns(df):
    """
    Removes columns that contain only 'N' (case-insensitive) or are completely NaN.
    Returns a cleaned DataFrame.
    """
    # Define a function to check if a column is all 'N' (case-insensitive)
    def is_all_N(col):
        # Convert to string, strip, and compare ignoring case
        return col.dropna().apply(lambda x: str(x).strip().lower() == 'n').all() if not col.dropna().empty else False

    # Columns to drop: either all values are NaN, or all 'N'
    columns_to_drop = [col for col in df.columns
                       if df[col].isna().all() or is_all_N(df[col])]
    df_cleaned = df.drop(columns=columns_to_drop)
    return df_cleaned