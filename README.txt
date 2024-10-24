# Stock Screening Project
---

# Stock Data Processor

This is a Python-based application that processes stock data, calculates specific growth and estimate metrics (`SG-F1`, `EG-F1`, `EG-F2`), and allows users to interact with the results via a Streamlit web interface.
 The app supports uploading stock data in CSV format, performs calculations based on predefined formulas, and provides downloadable reports of filtered results.

## Features

- **Flexible Data Input**: The application accepts CSV files with varying column order and dynamically detects necessary fields.
- **Calculations**:
  - `SG-F1`: Sales growth formula.
  - `EG-F1`: Earnings growth estimate between two fiscal periods (`F0` to `F1`).
  - `EG-F2`: Earnings growth estimate between two fiscal periods (`F1` to `F2`).
- **Outlier Filtering**: Automatically filters out stocks with extreme z-scores for the calculated metrics and removes invalid or missing data.
- **Downloadable Reports**: Provides options to download the following datasets:
  - Filtered stocks based on outliers.
  - Stocks with specific extreme values (`99`, `-99`, or `-100`).
  - Sector averages for the calculated metrics.
  - Stocks with extreme z-scores.

## Usage

1. **Upload CSV File**:
   - The application requires a CSV file as input. The file should contain the following columns (in any order):
     - `Company Name`
     - `Ticker`
     - `Market Cap (mil)`
     - `Sector`
     - `Industry`
     - `Exchange`
     - `Month of Fiscal Yr End`
     - `F0 Consensus Est.`
     - `F1 Consensus Est.`
     - `F2 Consensus Est.`
     - `Annual Sales ($mil)`
     - `F(1) Consensus Sales Est. ($mil)`

2. **Process Data**:
   - Once the file is uploaded, the application will automatically:
     - Detect the necessary columns regardless of their order.
     - Perform calculations for `SG-F1`, `EG-F1`, and `EG-F2` based on the provided formulas.
     - Filter out stocks with invalid or missing values necessary for the calculations.
     - Calculate sector-wise averages and perform outlier detection using z-scores.

3. **Download Results**:
   - After processing, you can download the following datasets:
     - Filtered stock data (removing extreme outliers).
     - Stocks with specific flag values (`99`, `-99`, `-100`).
     - Sector averages.
     - Stocks with extreme z-scores.

## Calculation Formulas

The following formulas are used to compute the stock metrics:

- **SG-F1** (Sales Growth):
  Formula:
  ```python
  SG-F1 = (F(1) Consensus Sales Est. ($mil) / Annual Sales ($mil)) - 1
  ```

- **EG-F1** (Earnings Growth for F0 → F1):
  Formula:
  ```python
  EG-F1 = IF(F0 < 0, IF(F1 > 0, 99, -99), IF(F0 > 0, IF(F1 < 0, -99, F1/F0 - 1), F1/F0 - 1))
  ```

- **EG-F2** (Earnings Growth for F1 → F2):
  Formula:
  ```python
  EG-F2 = IF(F1 < 0, IF(F2 > 0, 99, -99), IF(F1 > 0, IF(F2 < 0, -99, F2/F1 - 1), F2/F1 - 1))
  ```

## Error Handling

- The application logs errors and warnings during data processing. For example, if certain fields cannot be converted to numeric values, the row will be excluded from the analysis, and a warning will be logged.

## Known Limitations

- **Division by Zero**: The application filters out stocks where a division by zero would occur during calculations for `SG-F1`, `EG-F1`, or `EG-F2`.
- **Missing Data**: Rows with missing values for key columns (`F0`, `F1`, `F2`, `Annual Sales`, etc.) are automatically dropped from the analysis.

## Example

Here’s how the application looks when displaying results in Streamlit:

1. **Uploaded CSV Data**:
   - Displays the original data uploaded in CSV format.

2. **Processed Data**:
   - Shows the calculated values for `SG-F1`, `EG-F1`, and `EG-F2` formatted as percentages.

3. **Download Options**:
   - Provides buttons to download the filtered data, sector averages, and more.

4. **Script 2: Analyze Stocks in a Selected Sector**
   - Prompts the user for sector analysis criteria and performs the analysis.
   - Command to run: `python analyze_stocks.py`
   - Inputs: Filtered stock data CSV file and sector averages CSV file.
   - Outputs: Top-performing stocks CSV file and Excel file with applied coloring rules.
