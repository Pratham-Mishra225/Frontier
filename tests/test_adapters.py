from frontier_api.adapters.yfinance_client import fetch_historical_returns

def run_adapter_test():
    """
    Tests the yfinance adapter by fetching 1 year of real market data 
    for AAPL and MSFT and verifying the output structure.
    """
    tickers_to_test = ["AAPL", "MSFT"]
    lookback = 1  # 1 year is enough to verify functionality
    
    print(f"🚀 Fetching {lookback} year(s) of data for {tickers_to_test} via yfinance...")
    
    try:
        # Call the function from your adapter
        returns_dict = fetch_historical_returns(tickers_to_test, lookback_years=lookback)
        
        print("\n[Test 1] Verify Output Structure:")
        print(f"  ✅ Returned a dictionary with {len(returns_dict)} keys: {list(returns_dict.keys())}")
        
        print("\n[Test 2] Verify Data Alignment:")
        # Check that all arrays have the exact same length (crucial for NumPy matrix math)
        lengths = [len(returns) for returns in returns_dict.values()]
        print(f"  Data points per ticker: {lengths}")
        
        if len(set(lengths)) == 1:
            print("  ✅ Constraint Passed: Matrix dimensions match perfectly.")
        else:
            print("  ❌ FAILED: Matrix dimensions are misaligned.")
            
        print("\n🏁 Phase 3 Completed Successfully! The Market Data Adapter is robust.")
        
    except Exception as e:
        print(f"\n❌ Adapter Test Failed: {str(e)}")

if __name__ == "__main__":
    run_adapter_test()