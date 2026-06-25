# API Reference

Complete documentation for every public symbol in the `frontier` package.

---

## Top-Level Public API

Import these directly from `frontier`:

```python
from frontier import optimize, fetch_data
```

---

## `frontier.optimize`

**Alias for `frontier.core.optimizer.optimize_portfolio`.**

### Signature

```python
def optimize(
    returns_dict: Dict[str, List[float]],
    risk_free_rate: float = 0.04,
) -> dict:
```

### Description

The core optimization engine. Takes a dictionary of periodic return series and computes:

1. **Maximum Sharpe Ratio portfolio** — the portfolio that maximizes `(return - risk_free_rate) / volatility` subject to long-only, fully-invested constraints.
2. **Efficient Frontier curve** — up to 20 `(volatility, return)` coordinates spanning the attainable return range.

All statistics are **annualized** by multiplying daily means and covariance by 252.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `returns_dict` | `Dict[str, List[float]]` | *required* | Keys are asset identifiers (ticker symbols or any string). Values are lists of periodic returns (e.g., daily percentage returns as decimals: `0.01` = 1%). All lists must be the same length. |
| `risk_free_rate` | `float` | `0.04` | Annualized risk-free rate used as the Sharpe Ratio denominator baseline. Pass the current 3-month T-bill rate for realistic results. |

### Returns

```python
{
    "optimal_portfolio": {
        "sharpe_ratio": float,            # (return - rf) / volatility
        "expected_annual_return": float,  # annualized mean return
        "annual_volatility": float,       # annualized standard deviation
        "weights": {                      # asset → allocation fraction
            "AAPL": 0.1200,
            "GOOG": 0.8800,
            "MSFT": 0.0000,
        }
    },
    "frontier_curve": [                   # up to 20 points
        {"volatility": 0.2134, "return_rate": 0.1523},
        ...
    ]
}
```

All numeric values are rounded to 4 decimal places.

### Raises

| Exception | Condition |
|---|---|
| `ValueError` | Fewer than 2 assets in `returns_dict` |
| `ValueError` | Return series have different lengths |
| `ValueError` | Any asset has fewer than 2 observations |
| `frontier.exceptions.ConvergenceError` | SLSQP solver fails to converge on the Max-Sharpe sub-problem |

### Examples

**Minimal example:**

```python
from frontier import optimize

result = optimize({
    "AAPL": [0.010, 0.005, -0.002, 0.015, 0.008],
    "MSFT": [0.008, 0.010,  0.000, -0.005, 0.012],
    "GOOG": [-0.010, 0.020, 0.010, -0.015, 0.005],
})

print(result["optimal_portfolio"]["weights"])
# {"AAPL": 0.0, "GOOG": 1.0, "MSFT": 0.0}
```

**Custom risk-free rate:**

```python
result = optimize(returns, risk_free_rate=0.052)  # current Fed rate
```

**Accessing the frontier curve:**

```python
for point in result["frontier_curve"]:
    print(f"σ={point['volatility']:.3f}  r={point['return_rate']:.3f}")
```

---

## `frontier.fetch_data`

**Alias for `frontier.adapters.yfinance_client.fetch_historical_returns`.**

> Requires `pip install frontier-quant[data]`

### Signature

```python
def fetch_data(
    tickers: List[str],
    lookback_years: int = 3,
) -> Dict[str, List[float]]:
```

### Description

Fetches adjusted-close price history from Yahoo Finance via `yfinance`, computes daily percentage returns, and returns a cleaned `Dict[str, List[float]]` ready to pass directly into `optimize()`.

**Cleaning behaviour:**
- Tickers are uppercased and deduplicated
- NaN rows (e.g., from recent IPOs) are dropped before computing returns
- The first row of returns (always NaN from `pct_change`) is dropped
- If cleaning removes all rows, a descriptive `ValueError` is raised

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tickers` | `List[str]` | *required* | List of valid Yahoo Finance ticker symbols (e.g., `["AAPL", "MSFT"]`). Case-insensitive; converted to uppercase internally. Duplicates are removed. |
| `lookback_years` | `int` | `3` | Number of calendar years of history to fetch. The function uses `365.25 * lookback_years` days to account for leap years. |

### Returns

```python
Dict[str, List[float]]  # ticker → list of daily percentage returns
```

Keys are uppercase ticker symbols sorted alphabetically. Values are daily percentage returns as decimals (e.g., `0.0123` for a 1.23% day). All lists have the same length (post-cleaning).

### Raises

| Exception | Condition |
|---|---|
| `ValueError` | `tickers` list is empty |
| `ValueError` | Yahoo Finance returns no data (invalid tickers) |
| `ValueError` | All rows removed during NaN cleaning |
| `RuntimeError` | Network error connecting to Yahoo Finance |

### Example

```python
from frontier import fetch_data, optimize

returns = fetch_data(["AAPL", "MSFT", "GOOG"], lookback_years=3)

# Returns dict is ready for the optimizer
result = optimize(returns, risk_free_rate=0.04)
```

---

## `frontier.portfolio_performance`

**Also importable from `frontier.core.optimizer`.**

### Signature

```python
def portfolio_performance(
    weights: np.ndarray,
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
) -> Tuple[float, float]:
```

### Description

Computes **annualized portfolio return and volatility** for a given weight vector. This is a low-level helper used internally by `optimize_portfolio()`. Exposed for power users who want to evaluate arbitrary weight vectors against a pre-computed covariance matrix.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `weights` | `np.ndarray` | 1-D weight vector of shape `(n_assets,)`. Should sum to 1.0 for meaningful results. |
| `mean_returns` | `np.ndarray` | 1-D array of **annualized** mean returns, shape `(n_assets,)`. |
| `cov_matrix` | `np.ndarray` | 2-D **annualized** covariance matrix, shape `(n_assets, n_assets)`. |

### Returns

```python
Tuple[float, float]  # (annualized_return, annualized_volatility)
```

### Example

```python
import numpy as np
from frontier.core.optimizer import portfolio_performance

weights = np.array([0.5, 0.5])
mean_returns = np.array([0.10, 0.15])          # annualized
cov_matrix = np.array([[0.04, 0.01],
                        [0.01, 0.09]])          # annualized

ret, vol = portfolio_performance(weights, mean_returns, cov_matrix)
print(f"Return: {ret:.2%}  Volatility: {vol:.2%}")
# Return: 12.50%  Volatility: 20.00%
```

---

## `frontier.exceptions` Module

All Frontier exceptions inherit from `FrontierError`. Import from `frontier.exceptions`:

```python
from frontier.exceptions import FrontierError, ConvergenceError, DataAlignmentError
```

### Exception Hierarchy

```text
Exception
└── FrontierError                  # Base class for all Frontier errors
    ├── OptimizationError          # Optimizer-level failures
    │   └── ConvergenceError       # SLSQP failed to converge
    └── DataAlignmentError         # Incompatible input dimensions
```

### `FrontierError`

Base class. Catch this to handle any Frontier-specific error:

```python
from frontier.exceptions import FrontierError

try:
    result = optimize(my_returns)
except FrontierError as e:
    print(f"Frontier error: {e}")
```

### `OptimizationError`

Raised for unrecoverable errors within the optimization engine. Parent of `ConvergenceError`.

### `ConvergenceError`

Raised when the SLSQP solver runs but fails to find a satisfactory solution (i.e., `scipy.optimize.minimize` returns `success=False` on the Max-Sharpe sub-problem).

**When does this happen?**
- Highly correlated assets that make the covariance matrix nearly singular
- Very short return series (fewer than ~10 observations)
- Synthetic or constant returns with zero variance

```python
from frontier.exceptions import ConvergenceError

try:
    result = optimize(returns)
except ConvergenceError as e:
    print(f"Solver did not converge: {e}")
    # Inspect e.args[0] for the scipy diagnostic message
```

### `DataAlignmentError`

Raised when return series have incompatible dimensions. Currently documented for use by future adapters; the core optimizer raises `ValueError` directly for mismatched lengths in v0.1.

---

## Pydantic Models (`frontier.models.schemas`)

These models validate requests and responses for the FastAPI layer. They can also be used as data contracts in your own code.

### `OptimizeRequest`

```python
class OptimizeRequest(BaseModel):
    returns: Dict[str, List[float]]   # required
    risk_free_rate: float = 0.04      # optional, default 4%
```

Payload for `POST /v1/optimize`. `returns` must have at least 2 keys with equal-length value lists.

### `TickerOptimizeRequest`

```python
class TickerOptimizeRequest(BaseModel):
    tickers: List[str]          # required, min 2 items
    lookback_years: int = 3     # 1–20, default 3
    risk_free_rate: float = 0.04
```

Payload for `POST /v1/optimize_from_tickers`.

### `PortfolioMetrics`

```python
class PortfolioMetrics(BaseModel):
    sharpe_ratio: float
    expected_annual_return: float
    annual_volatility: float
    weights: Dict[str, float]   # sum to 1.0
```

### `FrontierPoint`

```python
class FrontierPoint(BaseModel):
    volatility: float
    return_rate: float   # named return_rate because 'return' is a Python keyword
```

### `OptimizeResponse`

```python
class OptimizeResponse(BaseModel):
    status: str = "success"
    metadata: dict = {}
    optimal_portfolio: PortfolioMetrics
    frontier_curve: List[FrontierPoint]
```

Response model for both `/v1/optimize` endpoints.

---

## REST API Endpoints

> Requires `pip install frontier-quant[server]`

### `GET /health`

Liveness probe. No authentication required.

**Response:**
```json
{"status": "active", "service": "Frontier API"}
```

---

### `POST /v1/optimize`

Pure-math endpoint. Accepts pre-calculated returns. No network calls made by the server.

**Request body:**
```json
{
  "returns": {
    "AAPL": [0.010, 0.005, -0.002, 0.015, 0.008],
    "MSFT": [0.008, 0.010,  0.000, -0.005, 0.012],
    "GOOG": [-0.010, 0.020, 0.010, -0.015, 0.005]
  },
  "risk_free_rate": 0.04
}
```

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `returns` | object | ✅ | — | ≥2 keys, equal-length arrays, ≥2 observations |
| `risk_free_rate` | number | ❌ | `0.04` | Any float |

**Response:** `OptimizeResponse` (see Pydantic models above)

**Error responses:**

| HTTP Status | Cause |
|---|---|
| `400` | Invalid returns data (e.g., single asset, mismatched lengths, convergence failure) |
| `422` | Missing required field or type mismatch |

---

### `POST /v1/optimize_from_tickers`

Convenience endpoint. Accepts ticker symbols, fetches data internally via yfinance.

> Requires yfinance to be installed (`pip install frontier-quant[all]`).

**Request body:**
```json
{
  "tickers": ["AAPL", "MSFT", "GOOG"],
  "lookback_years": 3,
  "risk_free_rate": 0.04
}
```

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `tickers` | array of string | ✅ | — | ≥2 items |
| `lookback_years` | integer | ❌ | `3` | 1–20 |
| `risk_free_rate` | number | ❌ | `0.04` | Any float |

**Response:** `OptimizeResponse` (same structure as `/v1/optimize`)

**Error responses:**

| HTTP Status | Cause |
|---|---|
| `400` | Invalid tickers, no data returned, or optimizer validation failure |
| `422` | Missing required field or type mismatch |
| `502` | Yahoo Finance connection failure (network error) |
| `500` | Unexpected server error |

---

## Package Metadata

```python
import frontier

frontier.__version__   # str — e.g. "0.1.0"
frontier.__author__    # str — "Pratham Mishra"
frontier.__license__   # str — "MIT"
```
