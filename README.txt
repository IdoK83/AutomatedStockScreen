# Stock Screening Project

## Overview
This project is designed to process stock data, filter out outliers, calculate sector averages, and perform stock analysis based on specified criteria. The project generates various outputs, including filtered stock data, sector averages, and top-performing stocks, all saved in CSV and Excel formats.

## Input File Structure
The input CSV file should contain the following columns:

- `Company Name`: Name of the company
- `Ticker`: Stock ticker symbol
- `Market Cap (mil)`: Market capitalization in millions
- `Sector`: Sector to which the company belongs
- `Industry`: Industry to which the company belongs
- `Exchange`: Stock exchange where the company is listed
- `Month of Fiscal Yr End`: Month of the fiscal year end
- `F0 Consensus Est.`: Current fiscal year consensus estimate
- `F1 Consensus Est.`: Next fiscal year consensus estimate
- `F2 Consensus Est.`: Following fiscal year consensus estimate
- `Annual Sales ($mil)`: Annual sales in millions
- `F(1) Consensus Sales Est. ($mil)`: Next fiscal year's consensus sales estimate in millions
- `SG-F1`: Sales growth forecast for the next fiscal year
- `EG-F1`: Earnings growth forecast for the next fiscal year
- `EG-F2`: Earnings growth forecast for the following fiscal year

I used Zacks stock screener to do so. Note that the order matters.

## Output Files
1. `filtered_stock_data.csv`: Contains the filtered stock data after removing outliers.
2. `stocks_99.csv`: Contains stocks with specific values (99).
3. `stocks_neg99.csv`: Contains stocks with specific negative values (-99).
4. `stocks_neg100.csv`: Contains stocks with specific negative values (-100).
5. `sector_averages.csv`: Contains the average growth expectations for each sector.
6. `sector_averages_colored.xlsx`: Contains the sector averages with applied coloring rules for better visualization
(Above average: green, Minimal: red).
7. `top_stocks_at_xyz_sector.csv`: Contains the top stocks at a sector, given the z-score that you able to "tolerate"
and the percentage of the sector that you want to take.

## Filtering Criteria
The project filters the stock data based on the following criteria:
- Removes rows where `SG-F1`, `EG-F1`, or `EG-F2` have specific values (99, -99, -100).
- Filters out rows where `SG-F1`, `EG-F1`, or `EG-F2` have NaN values.
- Applies robust z-score filtering to remove outliers based on a threshold (z-score > 3).

## Calculations
The project performs the following calculations:
1. **Robust Z-scores**: Calculates z-scores for `SG-F1`, `EG-F1`, and `EG-F2` using median and interquartile range (IQR) for robust scaling.
2. **Sector Averages**: Calculates the average values for `SG-F1`, `EG-F1`, and `EG-F2` for each sector.
3. **Weighted Scores**: Calculates a weighted score for each stock based on `SG-F1`, `EG-F1`, and `EG-F2` using specified weights.

## Analysis
The project performs stock analysis based on user-specified criteria:
- Filters and ranks stocks within a selected sector based on a z-score threshold and top percentage.
- Colors cells green if they exceed the average values and red if they are the minimum in their respective columns.

## Usage
1. **Script 1: Determine Best Performing Sectors**
   - Processes the stock data, filters out outliers, calculates sector averages, and saves the results.
   - Command to run: `python best_performance_sector.py`
   - Input: CSV file with the structure mentioned above.
   - Outputs: Filtered stock data, sector averages, and other intermediate files.

2. **Script 2: Analyze Stocks in a Selected Sector**
   - Prompts the user for sector analysis criteria and performs the analysis.
   - Command to run: `python analyze_stocks.py`
   - Inputs: Filtered stock data CSV file and sector averages CSV file.
   - Outputs: Top-performing stocks CSV file and Excel file with applied coloring rules.
