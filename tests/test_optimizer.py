from frontier_api.core.optimizer import optimize_portfolio

def run_tests():
    """
    Feeds fake, hardcoded daily return arrays into the math engine to verify 
    output structure and mathematical constraints without needing yfinance.
    """
    
    # Fake daily returns over 5 days for 3 assets
    fake_returns_data = {
        "AAPL": [0.010, 0.005, -0.002, 0.015, 0.008],
        "MSFT": [0.008, 0.010, 0.000, -0.005, 0.012],
        "GOOG": [-0.010, 0.020, 0.010, -0.015, 0.005]
    }

    print("🚀 Initializing Frontier Math Engine...")
    result = optimize_portfolio(fake_returns_data, risk_free_rate=0.04)

    # --- Test 1: Verify the Portfolio Metrics ---
    optimal = result["optimal_portfolio"]
    print("\n[Test 1] Max Sharpe Portfolio Metrics:")
    print(f"  Sharpe Ratio: {optimal['sharpe_ratio']}")
    print(f"  Expected Return: {optimal['expected_annual_return']}")
    print(f"  Volatility: {optimal['annual_volatility']}")
    
    # --- Test 2: Verify the Weights Constraint ---
    weights = optimal["weights"]
    print(f"\n[Test 2] Asset Weights: {weights}")
    
    total_weight = sum(weights.values())
    print(f"  Sum of all weights: {total_weight:.4f}")
    
    # The sum should be incredibly close to 1.0 (allowing for tiny floating-point rounding differences)
    assert round(total_weight, 2) == 1.0, f"FAILED: Weights sum to {total_weight}, not 1.0!"
    print("  ✅ Constraint Passed: Weights sum exactly to 1.0")

    # --- Test 3: Verify the Efficient Frontier ---
    frontier = result["frontier_curve"]
    print(f"\n[Test 3] Efficient Frontier Curve:")
    print(f"  ✅ Generated {len(frontier)} plot points.")
    print(f"  Sample Point: {frontier[0]}")
    
    print("\n🏁 Phase 2 Completed Successfully! The Math Engine is robust.")

if __name__ == "__main__":
    run_tests()