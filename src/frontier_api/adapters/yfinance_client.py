import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

def fetch_historical_returns(tickers: List[str], lookback_years: int = 3) -> Dict[str, List[float]]:
    """
    Fetches historical adjusted close prices for a list of tickers,
    cleans the data, calculates daily periodic returns, and formats
    the output to match the Frontier pure math engine's required input.
    """
    if not tickers:
        raise ValueError("Ticker list cannot be empty.")
    
    # Ensure tickers are uppercase and unique
    tickers = list(set([t.upper() for t in tickers]))

    end_date = datetime.today()
    # Using 365.25 to account for leap years
    start_date = end_date - timedelta(days=int(lookback_years * 365.25))

    # Fetch data from yfinance silently (progress=False)
    try:
        df = yf.download(tickers, start=start_date, end=end_date, progress=False)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch data from yfinance: {str(e)}")

    if df.empty:
        raise ValueError("No data returned from Yahoo Finance. Check if the ticker symbols are correct.")

    # yfinance returns a MultiIndex column dataframe if multiple tickers are passed.
    # We want the 'Adj Close' to account for stock splits and dividends.
    if 'Adj Close' in df:
        prices = df['Adj Close']
    elif 'Close' in df:
        prices = df['Close']
    else:
        raise ValueError("Expected 'Adj Close' or 'Close' in yfinance response.")

    # If only one ticker was passed (even though schemas enforce min_length=2, good for safety), 
    # prices will be a Series instead of a DataFrame. Convert it to standardize.
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])

    # ---------------------------------------------------------
    # The Cleaning Layer
    # ---------------------------------------------------------
    # If a user asks for [AAPL, MSFT, and a stock that IPO'd 1 year ago] with a 3-year lookback,
    # yfinance will return 3 years of rows, but the new stock will have NaNs for the first 2 years.
    # We MUST drop all rows with NaNs to ensure matrix dimensions match for the math engine.
    prices_clean = prices.dropna()

    if prices_clean.empty:
        raise ValueError(
            "Data cleaning removed all rows. This usually happens if one of the requested "
            "stocks did not exist for the entire lookback period."
        )

    # ---------------------------------------------------------
    # The Math Layer (Translating prices to periodic returns)
    # ---------------------------------------------------------
    # pct_change() calculates (Price_today - Price_yesterday) / Price_yesterday
    # The first row becomes NaN (no yesterday to compare to), so we dropna() again.
    returns_df = prices_clean.pct_change().dropna()

    # ---------------------------------------------------------
    # Formatting Layer (Matching the Phase 1 Schema)
    # ---------------------------------------------------------
    # Convert the Pandas DataFrame into the exact Dict[str, List[float]] structure
    returns_dict = {ticker: returns_df[ticker].tolist() for ticker in returns_df.columns}

    return returns_dict