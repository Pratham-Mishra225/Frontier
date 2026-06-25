# Architecture

This document explains Frontier's design decisions, module boundaries, and dependency rules. It is intended for contributors, integrators, and developers who need to understand the project internals.

---

## Design Philosophy: Library-First

Frontier was architected around one principle: **the math engine must have zero coupling to external services**.

Most portfolio optimization tools tie their data pipeline, optimizer, and API layer together. This makes them hard to test in isolation, impossible to embed in existing data pipelines, and brittle when a data provider changes its response format.

Frontier separates these concerns into four distinct layers that communicate only through plain Python types.

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        frontier.api                             │
│   FastAPI endpoints — HTTP, CORS, request validation            │
│   Depends on: core + adapters + models                          │
├─────────────────────────────────────────────────────────────────┤
│                      frontier.adapters                          │
│   External data source integrations (Yahoo Finance)             │
│   Depends on: (nothing inside frontier)                         │
├─────────────────────────────────────────────────────────────────┤
│                        frontier.core                            │
│   Pure NumPy/SciPy optimization engine                          │
│   Depends on: frontier.exceptions only                          │
├─────────────────────────────────────────────────────────────────┤
│              frontier.models  │  frontier.exceptions            │
│   Pydantic schemas            │   Typed exception hierarchy     │
│   Depends on: (nothing)       │   Depends on: (nothing)         │
└─────────────────────────────────────────────────────────────────┘
```

**Dependency flow (one direction only):**

```
frontier.exceptions ←── frontier.core ←── frontier.adapters ←── frontier.api
frontier.models     ←────────────────────────────────────────── frontier.api
```

No inner layer ever imports from an outer layer. `frontier.core` does not know that `yfinance` exists. `frontier.adapters` does not know that FastAPI exists.

---

## Module Responsibilities

### `frontier.core` — The Math Engine

**File:** `src/frontier/core/optimizer.py`

The pure optimization engine. It accepts `Dict[str, List[float]]` and returns `dict`. It has no awareness of where the data came from or where the result is going.

**What it does:**
1. Validates the input (≥2 assets, equal lengths, ≥2 observations)
2. Converts the returns dict into a NumPy matrix `(n_assets × n_observations)`
3. Computes annualized mean returns and covariance matrix (× 252)
4. Solves the Max-Sharpe sub-problem using SciPy SLSQP
5. Generates 20 Efficient Frontier points by solving 20 minimum-volatility sub-problems
6. Returns a structured plain dict matching `OptimizeResponse`

**Key implementation choices:**
- SLSQP was chosen over Monte Carlo because it finds the *exact* optimum deterministically and is much faster for small portfolios (2–30 assets)
- The closure bug in the frontier loop (`lambda x, t=target:`) is explicitly documented in the source
- All weights are rounded to 4 decimal places; internally they are full-precision floats
- `ConvergenceError` is raised only for the Max-Sharpe step (required); frontier curve failures are silently dropped

**Public functions:**
```python
optimize_portfolio(returns_dict, risk_free_rate=0.04) -> dict
portfolio_performance(weights, mean_returns, cov_matrix) -> Tuple[float, float]
```

---

### `frontier.adapters` — External Data

**File:** `src/frontier/adapters/yfinance_client.py`

Bridges Yahoo Finance data into the format `frontier.core` expects. It is **entirely optional** — the core works without it.

**What it does:**
1. Normalizes ticker input (uppercase, deduplicate, sort)
2. Calls `yf.download()` for adjusted-close prices
3. Handles both single-ticker (`pd.Series`) and multi-ticker (`pd.DataFrame`) responses
4. Drops NaN rows to handle IPO-date mismatches
5. Computes daily percentage returns via `pct_change()`
6. Returns `Dict[str, List[float]]` ready for `optimize_portfolio()`

**Key implementation choices:**
- Tickers are sorted alphabetically for deterministic output order
- `Adj Close` is preferred over `Close` to account for dividends and splits
- NaN cleaning is done *before* computing returns (not after), so IPO-date spikes are avoided
- The `progress=False` flag suppresses yfinance's terminal progress bar

**Why this is a separate layer:** If Yahoo Finance changes its API, only this file changes. The core optimizer and API layer are unaffected. Users with Bloomberg or proprietary feeds bypass this layer entirely.

---

### `frontier.models` — Data Contracts

**File:** `src/frontier/models/schemas.py`

Pydantic v2 models that define the shape of API requests and responses. They are used by the FastAPI layer for automatic validation and serialization, and can be used directly in user code as data contracts.

| Model | Purpose |
|---|---|
| `OptimizeRequest` | Payload for `POST /v1/optimize` |
| `TickerOptimizeRequest` | Payload for `POST /v1/optimize_from_tickers` |
| `PortfolioMetrics` | The `optimal_portfolio` sub-object in responses |
| `FrontierPoint` | A single `(volatility, return_rate)` point |
| `OptimizeResponse` | Full response envelope for both endpoints |

**Key implementation choices:**
- `return_rate` (not `return`) is used because `return` is a Python keyword
- `metadata` is `dict` with default `{}` — the field exists for future enrichment (data source, date range) without breaking the schema
- `TickerOptimizeRequest.lookback_years` is bounded `[1, 20]` at the Pydantic level, not just in docstrings

---

### `frontier.api` — HTTP Layer

**File:** `src/frontier/api/main.py`

The FastAPI application. Thin by design — it validates requests, delegates to `frontier.core` and `frontier.adapters`, and maps domain exceptions to appropriate HTTP status codes.

**Error mapping:**

| Exception | HTTP Status | Endpoint |
|---|---|---|
| `ValueError` (data) | 400 | Both |
| `ConvergenceError` | 400 | `/v1/optimize` |
| `RuntimeError` (network) | 502 | `/v1/optimize_from_tickers` |
| `Exception` (unexpected) | 500 | `/v1/optimize_from_tickers` |
| Pydantic `ValidationError` | 422 | Both (automatic) |

**CORS:** Wildcard `allow_origins=["*"]` is configured for development. For production deployments, replace `"*"` with your frontend's actual origin.

---

### `frontier.exceptions` — Exception Hierarchy

**File:** `src/frontier/exceptions.py`

```python
Exception
└── FrontierError                  # catch-all for library errors
    ├── OptimizationError          # optimizer-level failures
    │   └── ConvergenceError       # SLSQP did not converge
    └── DataAlignmentError         # series dimension mismatch
```

`DataAlignmentError` is documented but not yet raised by `v0.1` — the core validator raises `ValueError` directly. It exists as a forward declaration for when the adapter layer grows more sophisticated alignment logic.

---

## The Two-Endpoint Design

The API intentionally has **two separate endpoints** that serve different users:

| Endpoint | Who Uses It | Why |
|---|---|---|
| `POST /v1/optimize` | Institutions, quants with proprietary data | No internet calls. Send Bloomberg/Refinitiv data directly. |
| `POST /v1/optimize_from_tickers` | Frontend devs, rapid prototyping | One call: tickers in, weights out. |

Both return **identical response schemas**. A dashboard can switch between them without changing its rendering logic.

---

## Testability Design

The architecture was built to make testing trivial at every layer:

| Test File | Strategy |
|---|---|
| `test_optimizer.py` | Pure unit tests — no mocks, no I/O |
| `test_adapters.py` | Mocked `yf.download()` calls — offline |
| `test_api.py` | FastAPI `TestClient` + `unittest.mock.patch` — fully offline |
| `test_exceptions.py` | Direct exception instantiation |
| `test_full_workflow.py` | Live integration tests, `@pytest.mark.network`, skipped in CI |

CI runs `pytest -m "not network"` — 100% offline. The full suite including live calls runs locally.

---

## Data Flow Diagrams

### Pure Library Usage

```
User provides Dict[str, List[float]]
        │
        ▼
frontier.core.optimizer.optimize_portfolio()
        │
        ▼
Returns structured dict
        │
        ▼
User reads optimal_portfolio + frontier_curve
```

### Data Adapter + Optimizer

```
User calls fetch_data(["AAPL", "MSFT"], lookback_years=3)
        │
        ▼
frontier.adapters.yfinance_client.fetch_historical_returns()
  • yf.download() → DataFrame
  • dropna() → cleaned prices
  • pct_change() → daily returns
  • Returns Dict[str, List[float]]
        │
        ▼
frontier.core.optimizer.optimize_portfolio()
        │
        ▼
Returns structured dict
```

### FastAPI /v1/optimize_from_tickers

```
HTTP POST /v1/optimize_from_tickers
  { tickers: [...], lookback_years: 3, risk_free_rate: 0.04 }
        │
        ▼ Pydantic validates TickerOptimizeRequest
frontier.api.main.optimize_from_tickers()
        │
        ├── frontier.adapters.fetch_historical_returns()
        │       • On ValueError → HTTP 400
        │       • On RuntimeError → HTTP 502
        │
        └── frontier.core.optimize_portfolio()
                • On ConvergenceError → HTTP 400 (via generic Exception handler)
        │
        ▼
OptimizeResponse serialized to JSON
HTTP 200
```

---

## Dependency Graph by Extra

```
pip install frontier-quant           →  numpy, scipy, pydantic
pip install frontier-quant[data]     →  + yfinance, pandas
pip install frontier-quant[server]   →  + fastapi, uvicorn
pip install frontier-quant[all]      →  + yfinance, pandas, fastapi, uvicorn
pip install frontier-quant[dev]      →  + pytest, ruff, mypy, httpx, stubs
```

The install extras mirror the module boundaries exactly. You can ship `frontier.core` in a serverless function with a 10 MB dependency footprint, or the full stack in a Docker container — the same `pyproject.toml` controls both.

---

## Contributing: Extending the Architecture

### Adding a New Data Adapter (e.g., Bloomberg)

1. Create `src/frontier/adapters/bloomberg_client.py`
2. Implement `fetch_bloomberg_returns(tickers, ...) -> Dict[str, List[float]]`
3. Expose it from `frontier.adapters.__init__.py`
4. Add a `bloomberg` optional extra in `pyproject.toml`
5. Write mocked unit tests in `tests/test_adapters.py`

The optimizer requires no changes.

### Adding a New Optimization Strategy (e.g., Minimum Volatility)

1. Add a new function in `src/frontier/core/optimizer.py`
2. Extend `OptimizeResponse` in `frontier.models.schemas` if the output shape differs
3. Add a new endpoint in `frontier.api.main` if HTTP exposure is needed
4. Write pure unit tests for the new function

No adapter changes required.

### Adding a New API Endpoint

1. Add the route function in `src/frontier/api/main.py`
2. Add request/response Pydantic models in `frontier.models.schemas`
3. Map domain exceptions to appropriate HTTP codes
4. Add offline TestClient tests in `tests/test_api.py`
