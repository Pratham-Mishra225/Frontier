# Installation Guide

Frontier uses **optional extras** so that you only install the dependencies your workflow requires. The core optimizer has no network or HTTP dependencies.

---

## Requirements

- **Python**: 3.10, 3.11, or 3.12
- **pip**: 21.0+

---

## Install Options

### 1. Core Library Only

```bash
pip install frontier-quant
```

**What this installs:**
- `numpy >= 1.24.0` — vectorized matrix math
- `scipy >= 1.10.0` — SLSQP optimization solver
- `pydantic >= 2.0.0` — data validation and schemas

**What you get:** The `optimize()` function and the full optimization engine. You must supply your own return data as a `Dict[str, List[float]]`.

**Best for:** Quant analysts, Jupyter notebooks, production pipelines with proprietary data feeds.

---

### 2. Core + Yahoo Finance Data Adapter

```bash
pip install frontier-quant[data]
```

**Adds on top of core:**
- `yfinance >= 0.2.28` — Yahoo Finance historical data
- `pandas >= 2.0.0` — DataFrame processing

**What you get:** The `fetch_data()` function that pulls adjusted-close prices, computes daily percentage returns, and cleans IPO/NaN mismatches automatically.

**Best for:** Personal projects, research, rapid prototyping with public equities.

---

### 3. Core + FastAPI Server

```bash
pip install frontier-quant[server]
```

**Adds on top of core:**
- `fastapi >= 0.100.0` — async HTTP framework
- `uvicorn >= 0.23.0` — ASGI server

**What you get:** The `frontier.api.main:app` FastAPI application with two endpoints (`/v1/optimize` and `/v1/optimize_from_tickers`) plus automatic Swagger docs.

> **Note:** The `[server]` extra does **not** include `[data]`. The `/v1/optimize` endpoint works without `yfinance`. To use `/v1/optimize_from_tickers`, you must also install `[data]`.

**Best for:** Teams building portfolio dashboards or microservices that call the optimizer over HTTP.

---

### 4. All Production Extras

```bash
pip install frontier-quant[all]
```

Installs everything: `[data]` + `[server]`. Equivalent to:

```bash
pip install frontier-quant[data,server]
```

**Best for:** Full deployments where you want both the data adapter and the HTTP server.

---

## Development Installation

To contribute to Frontier or run the full test suite locally:

```bash
git clone https://github.com/Pratham-Mishra225/frontier-api.git
cd frontier-api

# Create a virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS / Linux)
source venv/bin/activate

# Install everything including dev tools
pip install -e ".[dev,data,server]"
```

**The `[dev]` extra installs:**
- `pytest`, `pytest-cov` — test runner and coverage
- `httpx` — async HTTP client for FastAPI TestClient
- `ruff` — linting and formatting
- `mypy` — static type checking
- `pandas-stubs`, `scipy-stubs` — type stubs for MyPy

---

## Verifying Your Installation

```python
import frontier

print(frontier.__version__)   # e.g. "0.1.0"
print(frontier.__author__)    # "Pratham Mishra"

# Quick sanity check
result = frontier.optimize({
    "A": [0.01, 0.02, -0.01, 0.03],
    "B": [0.02, -0.01, 0.01, 0.02],
})
print("OK:", "optimal_portfolio" in result)
```

---

## Python Version Support

| Python Version | Supported | CI Status |
|---|---|---|
| 3.10 | ✅ | Tested in CI |
| 3.11 | ✅ | Tested in CI |
| 3.12 | ✅ | Tested in CI |
| 3.9 and below | ❌ | Not supported (uses `match`, structural type hints) |
| 3.13 | 🔄 | Not yet tested |

---

## Installing from Source (Development Build)

```bash
git clone https://github.com/Pratham-Mishra225/frontier-api.git
cd frontier-api
pip install -e .
```

Editable mode (`-e`) means changes to `src/frontier/` are immediately reflected without reinstalling.

---

## Common Installation Issues

### `ModuleNotFoundError: No module named 'yfinance'`

You installed `frontier-quant` (core only) but called `fetch_data()`. Fix:

```bash
pip install frontier-quant[data]
```

### `ModuleNotFoundError: No module named 'fastapi'`

You installed `frontier-quant` or `frontier-quant[data]` but tried to run the server. Fix:

```bash
pip install frontier-quant[server]
```

### `ImportError` on Python 3.9

Frontier requires Python 3.10+. Upgrade your Python version or create a new venv with `python3.10`.

### yfinance version conflicts

If another package pins an older `yfinance`, install into a fresh venv:

```bash
python -m venv .venv-frontier
.venv-frontier/Scripts/activate
pip install frontier-quant[all]
```
