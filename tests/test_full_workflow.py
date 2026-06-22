from frontier_api.adapters.yfinance_client import fetch_historical_returns
from frontier_api.core.optimizer import optimize_portfolio

def run_integration_test():
    tickers = ["AAPL", "MSFT", "GOOG"]
    lookback = 3 
    
    print(f"🌐 STEP 1: Calling Market Data Adapter for {tickers}...")
    try:
        returns_dict = fetch_historical_returns(tickers, lookback_years=lookback)
        trading_days = len(list(returns_dict.values())[0])
        print(f"  ✅ Successfully retrieved data for {trading_days} trading days.")
        
        # --- NEW: Show the Yahoo Finance Data Preview ---
        print("\n  📊 Yahoo Finance Data Preview (First 3 daily returns):")
        for ticker, returns in returns_dict.items():
            print(f"    - {ticker}: {returns[:3]} ...")
            
        print(f"\n⚙️ STEP 2: Piping data into the Pure Math Engine...")
        result = optimize_portfolio(returns_dict, risk_free_rate=0.04)
        
        optimal = result["optimal_portfolio"]
        print("\n🏆 [FINAL OUTPUT] Maximum Sharpe Allocation:")
        print(f"  Sharpe Ratio: {optimal['sharpe_ratio']}")
        for ticker, weight in optimal["weights"].items():
            print(f"    - {ticker}: {weight * 100:.2f}%")
            
        # --- NEW: Explicitly loop and print all 20 points ---
        print(f"\n📈 Efficient Frontier ({len(result['frontier_curve'])} mapping points):")
        for i, point in enumerate(result['frontier_curve']):
            # Multiplying by 100 to show as clean percentages
            vol = point['volatility'] * 100
            ret = point['return_rate'] * 100
            print(f"  Point {i+1:02d} -> Risk (X): {vol:.2f}% | Reward (Y): {ret:.2f}%")

    except Exception as e:
        print(f"\n❌ Pipeline Failed: {str(e)}")

if __name__ == "__main__":
    run_integration_test()

    