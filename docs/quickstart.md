# Quick Start

Get your first portfolio optimization running in under 5 minutes.

---

## Prerequisites

Install Frontier first. If you just want the optimizer with no external data calls:

```bash
pip install frontier-quant
```

To also fetch live Yahoo Finance data:

```bash
pip install frontier-quant[data]
```

---

## Your First Optimization

### Step 1 — Prepare your returns data

The optimizer expects a `Dict[str, List[float]]` of periodic returns (typically daily percentage returns). All series must be the **same length** and contain **at least 2 observations**.

```python
returns = {
    "AAPL": [0.010,  0.005, -0.002,  0.015,  0.008,  0.003, -0.001,  0.012],
    "MSFT": [0.008,  0.010,  0.000, -0.005,  0.012,  0.007,  0.002,  0.009],
    "GOOG": [-0.010, 0.020,  0.010, -0.015,  0.005,  0.001,  0.018, -0.003],
}
```

> **Note:** With only 8 observations the optimizer produces mathematically valid but statistically meaningless results. Use 252+ daily observations (1 year) for anything you intend to act on.

### Step 2 — Call `optimize()`

```python
from frontier import optimize

result = optimize(returns, risk_free_rate=0.04)
```

`risk_free_rate` defaults to `0.04` (4% annualized). Pass the current 3-month T-bill rate for more accurate Sharpe ratios.

### Step 3 — Read the results

```python
portfolio = result["optimal_portfolio"]

print(f"Sharpe Ratio           : {portfolio['sharpe_ratio']:.4f}")
print(f"Expected Annual Return : {portfolio['expected_annual_return']:.1%}")
print(f"Annual Volatility      : {portfolio['annual_volatility']:.1%}")
print()
print("Optimal Weights:")
for ticker, weight in portfolio["weights"].items():
    print(f"  {ticker}: {weight:.1%}")

print()
print(f"Frontier curve points  : {len(result['frontier_curve'])}")
```

### Expected Output

```text
Sharpe Ratio           : 2.3939
Expected Annual Return : 168.0%
Annual Volatility      : 68.5%

Optimal Weights:
  AAPL: 0.0%
  GOOG: 100.0%
  MSFT: 0.0%

Frontier curve points  : 20
```

*(These extreme numbers are from 8 synthetic observations — they are correct outputs for this toy input.)*

---

## Fetching Real Market Data

Install the data adapter:

```bash
pip install frontier-quant[data]
```

Then:

```python
from frontier import fetch_data, optimize

# Fetch 3 years of daily adjusted-close returns for three tickers
returns = fetch_data(["AAPL", "MSFT", "GOOG"], lookback_years=3)

# The returns dict is ready to pass directly into optimize()
result = optimize(returns, risk_free_rate=0.04)

portfolio = result["optimal_portfolio"]
print(f"Sharpe: {portfolio['sharpe_ratio']:.4f}")
print(f"Weights: {portfolio['weights']}")
```

With 3 years of real data you should see a Sharpe ratio in the range of 0.5–2.0 depending on market conditions.

---

## Inspecting the Efficient Frontier

```python
from frontier import optimize

returns = {
    "AAPL": [0.010,  0.005, -0.002,  0.015,  0.008,  0.003, -0.001,  0.012],
    "MSFT": [0.008,  0.010,  0.000, -0.005,  0.012,  0.007,  0.002,  0.009],
    "GOOG": [-0.010, 0.020,  0.010, -0.015,  0.005,  0.001,  0.018, -0.003],
}

result = optimize(returns)

print("Efficient Frontier Coordinates:")
print(f"{'Volatility':>12}  {'Return':>10}")
print("-" * 26)
for point in result["frontier_curve"]:
    print(f"{point['volatility']:>12.4f}  {point['return_rate']:>10.4f}")
```

These `(volatility, return_rate)` pairs can be plotted directly with matplotlib:

```python
import matplotlib.pyplot as plt

x = [p["volatility"] for p in result["frontier_curve"]]
y = [p["return_rate"] for p in result["frontier_curve"]]

plt.figure(figsize=(9, 5))
plt.plot(x, y, "b-o", linewidth=2, markersize=4, label="Efficient Frontier")

opt = result["optimal_portfolio"]
plt.scatter(
    opt["annual_volatility"],
    opt["expected_annual_return"],
    color="red", s=100, zorder=5, label="Max Sharpe"
)

plt.xlabel("Annual Volatility (σ)")
plt.ylabel("Expected Annual Return")
plt.title("Efficient Frontier")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
```

---

## Common Mistakes

### ❌ Passing prices instead of returns

```python
# WRONG — these are prices, not returns
returns = {
    "AAPL": [182.50, 184.20, 181.00, 186.30],
    "MSFT": [380.10, 382.40, 379.50, 385.20],
}
```

```python
# CORRECT — percentage returns (price_today / price_yesterday - 1)
returns = {
    "AAPL": [0.0093, -0.0174, 0.0293],
    "MSFT": [0.0061, -0.0076, 0.0150],
}
```

If you have price data, convert it first:

```python
import pandas as pd

prices = pd.DataFrame({"AAPL": [182.50, 184.20, 181.00, 186.30]})
returns_df = prices.pct_change().dropna()
returns_dict = {col: returns_df[col].tolist() for col in returns_df.columns}
```

### ❌ Series with mismatched lengths

```python
# WRONG — AAPL has 5 observations, MSFT has 4
returns = {
    "AAPL": [0.01, 0.02, -0.01, 0.03, 0.01],
    "MSFT": [0.02, -0.01, 0.01, 0.02],         # ← one row shorter
}
# Raises: ValueError: All return series must have the same length.
```

Use `fetch_data()` — it automatically aligns and trims series to the shortest common window.

### ❌ Only one asset

```python
# WRONG — portfolio theory requires at least 2 assets
returns = {"AAPL": [0.01, 0.02, -0.01]}
# Raises: ValueError: At least 2 assets are required for portfolio optimization.
```

### ❌ Forgetting to install the data extra

```python
from frontier import fetch_data   # ImportError if [data] not installed
```

Fix: `pip install frontier-quant[data]`

### ❌ Forgetting to install the server extra before running uvicorn

```bash
uvicorn frontier.api.main:app  # ModuleNotFoundError: No module named 'fastapi'
```

Fix: `pip install frontier-quant[server]`

---

## Next Steps

- **More examples** → [Examples](examples.md)
- **Full function signatures** → [API Reference](api-reference.md)
- **Deploying the server** → [Examples — FastAPI Usage](examples.md#example-3-fastapi-server-usage)
- **Project internals** → [Architecture](architecture.md)
