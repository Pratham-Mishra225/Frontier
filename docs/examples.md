# Examples

Four complete, copy-paste runnable workflows covering the most common Frontier use cases.

---

## Example 1: Pure Optimization Workflow

**Scenario:** You have your own return data (from a database, Bloomberg, or a CSV file) and want to find the optimal portfolio weights. No internet connection required.

**Install:** `pip install frontier-api`

```python
"""
Example 1: Pure optimization workflow — bring your own data.

No network calls. Works with any return data source.
Install: pip install frontier-api
"""

from frontier import optimize

# --- Prepare your returns ---
# Replace these with your actual return series.
# Each value is a daily percentage return as a decimal.
# e.g., a 1.5% day is 0.015
returns = {
    "AAPL": [
        0.0123, -0.0045,  0.0234, -0.0012,  0.0189,
        0.0067, -0.0034,  0.0145,  0.0023, -0.0078,
        0.0201,  0.0034, -0.0023,  0.0156,  0.0089,
        -0.0112, 0.0234,  0.0045, -0.0067,  0.0123,
    ],
    "MSFT": [
        0.0098, -0.0023,  0.0178,  0.0034,  0.0145,
        0.0056, -0.0012,  0.0112,  0.0067, -0.0045,
        0.0167,  0.0023, -0.0034,  0.0134,  0.0078,
        -0.0089, 0.0198,  0.0034, -0.0045,  0.0098,
    ],
    "GOOG": [
        0.0145, -0.0067,  0.0256, -0.0023,  0.0201,
        0.0089, -0.0056,  0.0167,  0.0034, -0.0112,
        0.0223,  0.0045, -0.0012,  0.0178,  0.0101,
        -0.0134, 0.0267,  0.0056, -0.0089,  0.0145,
    ],
    "AMZN": [
        0.0178, -0.0089,  0.0289, -0.0034,  0.0234,
        0.0112, -0.0067,  0.0189,  0.0045, -0.0134,
        0.0245,  0.0056, -0.0023,  0.0201,  0.0123,
        -0.0156, 0.0298,  0.0067, -0.0112,  0.0167,
    ],
}

# --- Run optimization ---
result = optimize(returns, risk_free_rate=0.04)

# --- Read results ---
portfolio = result["optimal_portfolio"]

print("=" * 50)
print("OPTIMAL PORTFOLIO (Maximum Sharpe Ratio)")
print("=" * 50)
print(f"Expected Annual Return : {portfolio['expected_annual_return']:.2%}")
print(f"Annual Volatility      : {portfolio['annual_volatility']:.2%}")
print(f"Sharpe Ratio           : {portfolio['sharpe_ratio']:.4f}")
print()
print("Asset Allocations:")
for ticker, weight in sorted(portfolio["weights"].items()):
    bar = "█" * int(weight * 40)
    print(f"  {ticker:6s}  {weight:6.1%}  {bar}")

print()
print(f"Efficient Frontier: {len(result['frontier_curve'])} points computed")
print(f"  Min volatility: {min(p['volatility'] for p in result['frontier_curve']):.4f}")
print(f"  Max return:     {max(p['return_rate'] for p in result['frontier_curve']):.4f}")
```

**Expected output (approximate):**

```text
==================================================
OPTIMAL PORTFOLIO (Maximum Sharpe Ratio)
==================================================
Expected Annual Return : 638.80%
Annual Volatility      : 260.60%
Sharpe Ratio           : 2.4393

Asset Allocations:
  AAPL    0.0%
  AMZN  100.0%  ████████████████████████████████████████
  GOOG    0.0%
  MSFT    0.0%

Efficient Frontier: 20 points computed
  Min volatility: 0.2474
  Max return:     2.8340
```

> *These numbers are high because 20 observations is too few for meaningful statistics. With 1–3 years of daily data (~252–756 observations), expect annual returns in the range of 10–40% and volatilities of 15–35% for typical US equities.*

---

## Example 2: Yahoo Finance Workflow

**Scenario:** You want to optimize a real portfolio using live market data fetched from Yahoo Finance.

**Install:** `pip install frontier-api[data]`

```python
"""
Example 2: Yahoo Finance workflow — live market data.

Fetches 3 years of adjusted-close prices and optimizes.
Install: pip install frontier-api[data]
Requires: internet connection
"""

from frontier import fetch_data, optimize

# --- Configuration ---
TICKERS = ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA"]
LOOKBACK_YEARS = 3
RISK_FREE_RATE = 0.04   # current approximate 3-month T-bill rate

print(f"Fetching {LOOKBACK_YEARS} years of data for: {', '.join(TICKERS)}")
print("Please wait...\n")

# --- Fetch data ---
try:
    returns = fetch_data(TICKERS, lookback_years=LOOKBACK_YEARS)
except ValueError as e:
    print(f"Data error: {e}")
    raise
except RuntimeError as e:
    print(f"Network error: {e}")
    raise

print(f"Data retrieved. Observations per asset: {len(next(iter(returns.values())))}")

# --- Optimize ---
result = optimize(returns, risk_free_rate=RISK_FREE_RATE)

# --- Display results ---
portfolio = result["optimal_portfolio"]

print()
print("=" * 60)
print("OPTIMAL PORTFOLIO — Maximum Sharpe Ratio")
print("=" * 60)
print(f"Expected Annual Return : {portfolio['expected_annual_return']:.2%}")
print(f"Annual Volatility (σ)  : {portfolio['annual_volatility']:.2%}")
print(f"Sharpe Ratio           : {portfolio['sharpe_ratio']:.4f}")
print()

print("Asset Allocations:")
for ticker, weight in sorted(portfolio["weights"].items(), key=lambda x: -x[1]):
    bar = "█" * int(weight * 30)
    print(f"  {ticker:6s}  {weight:6.1%}  {bar}")

print()
print(f"Efficient Frontier — {len(result['frontier_curve'])} points")
print(f"{'Point':>6}  {'Volatility':>12}  {'Return':>10}")
print("-" * 34)
for i, point in enumerate(result["frontier_curve"]):
    print(f"  {i+1:>3}   {point['volatility']:>12.4f}  {point['return_rate']:>10.4f}")
```

**Expected output (approximate, based on real market data):**

```text
Fetching 3 years of data for: AAPL, MSFT, GOOG, AMZN, NVDA
Please wait...

Data retrieved. Observations per asset: 754

============================================================
OPTIMAL PORTFOLIO — Maximum Sharpe Ratio
============================================================
Expected Annual Return :  54.32%
Annual Volatility (σ)  :  30.18%
Sharpe Ratio           :  1.6686

Asset Allocations:
  NVDA    72.4%  █████████████████████
  MSFT    18.2%  █████
  AAPL     9.4%  ██
  AMZN     0.0%
  GOOG     0.0%

Efficient Frontier — 20 points
 Point    Volatility      Return
----------------------------------
    1        0.2412      0.1523
    2        0.2418      0.1773
   ...
   20        0.3890      0.5432
```

---

## Example 3: FastAPI Server Usage

**Scenario:** You want to deploy Frontier as a microservice that other applications can call over HTTP.

**Install:** `pip install frontier-api[all]`

### Starting the server

```bash
uvicorn frontier.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

### Endpoint 1: `/v1/optimize` — Bring Your Own Data

```bash
# Using curl
curl -X POST http://localhost:8000/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "returns": {
      "AAPL": [0.0123, -0.0045, 0.0234, -0.0012, 0.0189,
               0.0067, -0.0034, 0.0145, 0.0023, -0.0078],
      "MSFT": [0.0098, -0.0023, 0.0178, 0.0034, 0.0145,
               0.0056, -0.0012, 0.0112, 0.0067, -0.0045],
      "GOOG": [0.0145, -0.0067, 0.0256, -0.0023, 0.0201,
               0.0089, -0.0056, 0.0167, 0.0034, -0.0112]
    },
    "risk_free_rate": 0.04
  }'
```

**Response:**

```json
{
  "status": "success",
  "metadata": {},
  "optimal_portfolio": {
    "sharpe_ratio": 2.4012,
    "expected_annual_return": 0.6712,
    "annual_volatility": 0.2671,
    "weights": {
      "AAPL": 0.0,
      "GOOG": 1.0,
      "MSFT": 0.0
    }
  },
  "frontier_curve": [
    {"volatility": 0.2134, "return_rate": 0.1523},
    {"volatility": 0.2198, "return_rate": 0.1733},
    "..."
  ]
}
```

### Endpoint 2: `/v1/optimize_from_tickers` — One-Step Convenience

```bash
# Using curl
curl -X POST http://localhost:8000/v1/optimize_from_tickers \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOG", "AMZN"],
    "lookback_years": 3,
    "risk_free_rate": 0.04
  }'
```

### Calling from Python

```python
"""
Example 3b: Calling the Frontier API from Python using httpx.
"""

import httpx

BASE_URL = "http://localhost:8000"

# --- Health check ---
health = httpx.get(f"{BASE_URL}/health")
print("Server status:", health.json()["status"])

# --- Pure math optimization ---
response = httpx.post(
    f"{BASE_URL}/v1/optimize",
    json={
        "returns": {
            "AAPL": [0.0123, -0.0045, 0.0234, -0.0012, 0.0189,
                     0.0067, -0.0034, 0.0145, 0.0023, -0.0078],
            "MSFT": [0.0098, -0.0023, 0.0178, 0.0034, 0.0145,
                     0.0056, -0.0012, 0.0112, 0.0067, -0.0045],
        },
        "risk_free_rate": 0.04,
    },
    timeout=30.0,
)

if response.status_code == 200:
    data = response.json()
    portfolio = data["optimal_portfolio"]
    print(f"Sharpe: {portfolio['sharpe_ratio']:.4f}")
    print(f"Weights: {portfolio['weights']}")
else:
    print(f"Error {response.status_code}: {response.json()['detail']}")
```

### Calling from JavaScript (Fetch API)

```javascript
// Example 3c: Calling Frontier from a browser/Node.js frontend

async function optimizePortfolio(tickers, lookbackYears = 3) {
  const response = await fetch('http://localhost:8000/v1/optimize_from_tickers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tickers: tickers,
      lookback_years: lookbackYears,
      risk_free_rate: 0.04,
    }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(`Frontier API error: ${err.detail}`);
  }

  const data = await response.json();
  return data;
}

// Usage
const result = await optimizePortfolio(['AAPL', 'MSFT', 'GOOG']);
console.log('Optimal weights:', result.optimal_portfolio.weights);
console.log('Frontier points:', result.frontier_curve.length);
```

---

## Example 4: Hybrid Usage

**Scenario:** You want to use the data adapter to fetch real data, inspect the intermediate returns object, then pass it directly into the optimizer — without going through HTTP.

**Install:** `pip install frontier-api[data]`

```python
"""
Example 4: Hybrid — adapter + optimizer as a library, no HTTP.

Demonstrates how fetch_data() and optimize() compose directly,
and how to inspect and modify the intermediate returns dict.
"""

from frontier import fetch_data, optimize
from frontier.exceptions import ConvergenceError

# --- Step 1: Fetch data ---
print("Fetching data...")
raw_returns = fetch_data(
    tickers=["AAPL", "MSFT", "GOOG", "TSLA"],
    lookback_years=2,
)

# --- Step 2: Inspect before optimizing ---
print(f"\nAssets fetched: {list(raw_returns.keys())}")
print(f"Observations per asset: {len(next(iter(raw_returns.values())))}")

# Compute some basic stats before optimizing
for ticker, rets in sorted(raw_returns.items()):
    n = len(rets)
    mean_daily = sum(rets) / n
    # Annualize
    mean_annual = mean_daily * 252
    print(f"  {ticker}: mean daily={mean_daily:.4f}, annualized={mean_annual:.2%}")

# --- Step 3: Filter out high-volatility assets if desired ---
# This shows how you can manipulate the returns dict before optimization
import statistics

filtered_returns = {
    ticker: rets
    for ticker, rets in raw_returns.items()
    if statistics.stdev(rets) < 0.025  # exclude assets with daily vol > 2.5%
}

print(f"\nFiltered to {len(filtered_returns)} assets "
      f"(removed high-volatility assets): {list(filtered_returns.keys())}")

# Guard: we need at least 2 assets after filtering
if len(filtered_returns) < 2:
    print("Not enough assets after filtering — using full set.")
    filtered_returns = raw_returns

# --- Step 4: Optimize ---
try:
    result = optimize(filtered_returns, risk_free_rate=0.04)
except ConvergenceError as e:
    print(f"Optimizer did not converge: {e}")
    raise

# --- Step 5: Use the results ---
portfolio = result["optimal_portfolio"]
print("\n--- Optimization Result ---")
print(f"Sharpe Ratio           : {portfolio['sharpe_ratio']:.4f}")
print(f"Expected Annual Return : {portfolio['expected_annual_return']:.2%}")
print(f"Annual Volatility      : {portfolio['annual_volatility']:.2%}")
print("\nWeights:")
for ticker, weight in sorted(portfolio["weights"].items(), key=lambda x: -x[1]):
    print(f"  {ticker}: {weight:.4f} ({weight:.1%})")

# --- Step 6: Plot the frontier (requires matplotlib) ---
try:
    import matplotlib.pyplot as plt

    xs = [p["volatility"] for p in result["frontier_curve"]]
    ys = [p["return_rate"] for p in result["frontier_curve"]]

    plt.figure(figsize=(10, 6))
    plt.plot(xs, ys, "b-o", linewidth=2, markersize=5, label="Efficient Frontier")
    plt.scatter(
        portfolio["annual_volatility"],
        portfolio["expected_annual_return"],
        color="red", s=120, zorder=5, label="Max Sharpe Portfolio"
    )
    plt.xlabel("Annual Volatility (σ)")
    plt.ylabel("Expected Annual Return")
    plt.title("Efficient Frontier — Frontier Library")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("frontier.png", dpi=150)
    print("\nFrontier plot saved to frontier.png")
except ImportError:
    print("\n(Install matplotlib to generate the frontier plot)")
```

---

## Error Handling Reference

All examples should handle these exceptions in production:

```python
from frontier import optimize, fetch_data
from frontier.exceptions import ConvergenceError, FrontierError

try:
    returns = fetch_data(tickers, lookback_years=3)
    result = optimize(returns)

except ValueError as e:
    # Bad input: wrong tickers, mismatched series, too few assets
    print(f"Input error: {e}")

except ConvergenceError as e:
    # SLSQP solver failed — try with more data or different assets
    print(f"Solver error: {e}")

except RuntimeError as e:
    # Network failure from yfinance
    print(f"Network error: {e}")

except FrontierError as e:
    # Catch-all for any other Frontier library error
    print(f"Frontier error: {e}")
```
