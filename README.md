# Frontier

**Stateless, high-performance Mean-Variance portfolio optimization — as a Python library and a deployable FastAPI service.**

[![CI](https://github.com/Pratham-Mishra225/frontier-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Pratham-Mishra225/frontier-api/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/frontier-quant.svg)](https://pypi.org/project/frontier-quant/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Coverage: 92%](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)](#testing)

Frontier implements Modern Portfolio Theory (MPT) as a **library-first** package. A quant analyst can `import frontier` and pass in any returns data — no internet connection required. Optionally, install the `[data]` extra to pull live prices from Yahoo Finance, or the `[server]` extra to expose the entire engine as a production-ready REST API.

---

## Features

| Feature | Description |
|---|---|
| **Mean-Variance Optimization** | Markowitz SLSQP solver with long-only, fully-invested constraints |
| **Maximum Sharpe Portfolio** | Finds the exact portfolio maximizing risk-adjusted return for any risk-free rate |
| **Efficient Frontier Generation** | Returns 20 optimized `(volatility, return)` coordinates for charting |
| **FastAPI Service Layer** | Two production endpoints — pure-math and ticker-driven — with full CORS and OpenAPI docs |
| **Full Type Coverage** | `py.typed` marker shipped; all public functions annotated; MyPy-clean |
| **Modular Extras** | Install only what you need: core math, data adapter, or HTTP server |
| **PyPI Distribution** | `pip install frontier-quant` — no build step required |
| **92% Test Coverage** | Offline unit tests, mocked API tests, and optional live network tests |

---

## Installation

Frontier uses **optional extras** so you install only the dependencies your workflow requires.

### Core Library (pure math — no network, no server)

```bash
pip install frontier-quant
```

Installs: `numpy`, `scipy`, `pydantic`.  
Use this when you already have your own return data and want the optimizer only.

### With the Data Adapter

```bash
pip install frontier-quant[data]
```

Adds: `yfinance`, `pandas`.  
Use this to fetch live adjusted-close prices from Yahoo Finance.

### With the FastAPI Server

```bash
pip install frontier-quant[server]
```

Adds: `fastapi`, `uvicorn`.  
Use this to run Frontier as a local or containerized REST API.

### Full Runtime (data + server)

```bash
pip install frontier-quant[all]
```

Installs all production extras (`data` + `server`). Does **not** include dev tools.
Ideal for full deployments.

### Development Setup

```bash
git clone https://github.com/Pratham-Mishra225/frontier-api.git
cd frontier-api
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Installs the package in editable mode with all extras + dev tools
pip install -r requirements-dev.txt
# Equivalent to:
# pip install -e ".[all,dev]"
```

> **Requires Python 3.10, 3.11, or 3.12.** CI runs all three.

---

## Quick Start

### Option A — Pure Library (bring your own data)

```python
from frontier import optimize

# Provide pre-calculated daily log or percentage returns
returns = {
    "AAPL": [0.010,  0.005, -0.002,  0.015,  0.008, 0.003, -0.001,  0.012],
    "MSFT": [0.008,  0.010,  0.000, -0.005,  0.012, 0.007,  0.002,  0.009],
    "GOOG": [-0.010, 0.020,  0.010, -0.015,  0.005, 0.001,  0.018, -0.003],
}

result = optimize(returns, risk_free_rate=0.04)

print("Max Sharpe weights:")
for ticker, weight in result["optimal_portfolio"]["weights"].items():
    print(f"  {ticker}: {weight:.1%}")

print(f"\nExpected annual return : {result['optimal_portfolio']['expected_annual_return']:.1%}")
print(f"Annual volatility      : {result['optimal_portfolio']['annual_volatility']:.1%}")
print(f"Sharpe ratio           : {result['optimal_portfolio']['sharpe_ratio']:.4f}")
print(f"Frontier points        : {len(result['frontier_curve'])}")
```

**Expected output:**

```text
Max Sharpe weights:
  AAPL: 0.0%
  GOOG: 100.0%
  MSFT: 0.0%

Expected annual return : 168.0%
Annual volatility      : 68.5%
Sharpe ratio           : 2.3939
Frontier points        : 20
```

> *Note: toy data (8 observations) produces unrealistic numbers. Use 252+ daily observations or real data for meaningful results.*

### Option B — With Yahoo Finance Data Adapter

```bash
pip install frontier-quant[data]
```

```python
from frontier import fetch_data, optimize

# fetch_data is lazily loaded — the yfinance adapter is only imported
# when this function is actually called, keeping the core install lightweight.
returns = fetch_data(["AAPL", "MSFT", "GOOG"], lookback_years=3)

result = optimize(returns, risk_free_rate=0.04)

print("Optimal weights:")
for ticker, w in result["optimal_portfolio"]["weights"].items():
    print(f"  {ticker}: {w:.1%}")
```

> **Note:** Calling `fetch_data` without the `[data]` extra installed raises an `ImportError`
> with clear installation instructions — it never silently fails.

### Option C — As a REST API

```bash
pip install frontier-quant[server]
uvicorn frontier.api.main:app --reload
```

The server starts with **only the `[server]` extra**. The `/v1/optimize` endpoint
works immediately. If `/v1/optimize_from_tickers` is called without `[data]` installed,
it returns **HTTP 501** with a clear install instruction — the server never crashes.

To enable the ticker endpoint:

```bash
pip install frontier-quant[server] frontier-quant[data]
# or:
pip install frontier-quant[all]
```

Then in another terminal:

```bash
curl -X POST http://localhost:8000/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "returns": {
      "AAPL": [0.010, 0.005, -0.002, 0.015, 0.008],
      "MSFT": [0.008, 0.010,  0.000, -0.005, 0.012]
    },
    "risk_free_rate": 0.04
  }'
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

---

## Example Output

A real optimization over 3 years of daily data for AAPL / MSFT / GOOG returns a response like:

```json
{
  "status": "success",
  "metadata": {},
  "optimal_portfolio": {
    "sharpe_ratio": 1.2534,
    "expected_annual_return": 0.3841,
    "annual_volatility": 0.2748,
    "weights": {
      "AAPL": 0.1200,
      "GOOG": 0.8800,
      "MSFT": 0.0000
    }
  },
  "frontier_curve": [
    { "volatility": 0.2134, "return_rate": 0.1523 },
    { "volatility": 0.2198, "return_rate": 0.1733 },
    "... 18 more points ..."
  ]
}
```

---

## Architecture Overview

Frontier is designed around a strict **one-way dependency rule**:

```
frontier.models  ←──  frontier.core  ←──  frontier.adapters  ←──  frontier.api
    (schemas)         (optimizer)          (yfinance)              (FastAPI)
```

No inner layer may import from an outer layer.

| Module | Responsibility | Key Dependencies |
|---|---|---|
| `frontier.models` | Pydantic request/response schemas | `pydantic` |
| `frontier.core` | Pure numerical optimization engine | `numpy`, `scipy` |
| `frontier.adapters` | Yahoo Finance data retrieval + cleaning | `yfinance`, `pandas` |
| `frontier.api` | FastAPI HTTP endpoints + CORS | `fastapi`, `uvicorn` |
| `frontier.exceptions` | Typed exception hierarchy | — |

**`frontier.core` is intentionally isolated.** It knows nothing about the internet, tickers, or HTTP. It receives a `Dict[str, List[float]]` and returns a structured dict. This makes it trivially testable, embeddable, and replaceable.

---

## Project Structure

```text
frontier-api/
├── pyproject.toml              # Build config, extras, tool settings
├── README.md
├── LICENSE
├── docs/
│   ├── index.md                # Documentation hub
│   ├── installation.md         # Detailed install guide
│   ├── quickstart.md           # First steps and examples
│   ├── api-reference.md        # Full public API documentation
│   ├── architecture.md         # Design decisions and dependency flow
│   └── examples.md             # Copy-paste runnable examples
├── tests/
│   ├── conftest.py             # Shared fixtures and markers
│   ├── test_optimizer.py       # Core optimizer unit tests
│   ├── test_adapters.py        # yfinance adapter tests (mocked)
│   ├── test_api.py             # FastAPI endpoint tests (fully offline)
│   ├── test_exceptions.py      # Exception hierarchy tests
│   ├── test_isolation.py       # Dependency isolation regression tests (v0.1.2)
│   └── test_full_workflow.py   # Live integration tests (@network)
├── CHANGELOG.md                # Release history
├── requirements-dev.txt        # Developer convenience: -e .[all,dev]
└── src/
    └── frontier/
        ├── __init__.py         # Public API: optimize, fetch_data
        ├── py.typed            # PEP 561 marker
        ├── exceptions.py       # FrontierError, ConvergenceError, ...
        ├── core/
        │   └── optimizer.py    # optimize_portfolio, portfolio_performance
        ├── adapters/
        │   └── yfinance_client.py  # fetch_historical_returns (lazy imports)
        ├── models/
        │   └── schemas.py      # OptimizeRequest, OptimizeResponse, ...
        └── api/
            └── main.py         # FastAPI app, /v1/optimize, /v1/optimize_from_tickers
```

---

## Development

### Set Up Environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# or: source venv/bin/activate  # macOS / Linux

# Install package in editable mode with all extras + dev tools
pip install -r requirements-dev.txt
# Equivalent to: pip install -e ".[all,dev]"
```

### Run Tests

```bash
# Fast offline suite (CI mode — skips live Yahoo Finance calls)
pytest -m "not network"

# Full suite including live network tests
pytest

# With coverage report
pytest --cov=frontier --cov-report=term-missing -m "not network"

# A single module
pytest tests/test_optimizer.py -v
```

### Lint and Type-Check

```bash
# Ruff — linting and formatting
ruff check .
ruff format .

# MyPy — static type checking
mypy src
```

### Run the Dev Server

```bash
uvicorn frontier.api.main:app --reload
```

Open `http://localhost:8000/docs` for Swagger UI or `http://localhost:8000/redoc` for ReDoc.

---

## CI/CD

GitHub Actions runs on every push to `main` and every pull request.

**Workflow** (`.github/workflows/ci.yml`):

1. **Matrix**: Python 3.10, 3.11, 3.12 — each in its own job
2. **Install**: `pip install -e ".[all,dev]"` — all runtime extras + dev tools
3. **Ruff**: linting (`ruff check .`)
4. **MyPy**: static typing (`mypy src`)
5. **Tests**: offline suite (`pytest -m "not network"`)

Live Yahoo Finance tests are marked `@pytest.mark.network` and excluded from CI. Run them locally with `pytest` (no `-m` flag).

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Liveness probe |
| `POST` | `/v1/optimize` | None | Pure-math endpoint — bring your own returns |
| `POST` | `/v1/optimize_from_tickers` | None | Convenience endpoint — pass tickers, get results |

Interactive docs automatically available at `/docs` (Swagger) and `/redoc` (ReDoc).

See [`docs/api-reference.md`](docs/api-reference.md) for full parameter and response documentation.

---

## Roadmap

### v0.1 ✅ Released
- Mean-variance optimization engine (SLSQP)
- Maximum Sharpe portfolio
- Efficient frontier (20 points)
- Yahoo Finance data adapter
- FastAPI service with two endpoints
- 92% test coverage
- MyPy + Ruff clean
- CI on Python 3.10 / 3.11 / 3.12
- TestPyPI distribution

### v0.2 — Planned
- [ ] Minimum volatility portfolio endpoint
- [ ] Portfolio analytics (Sortino ratio, max drawdown, beta)
- [ ] Frontier visualization helpers (matplotlib / plotly)
- [ ] Portfolio comparison (multiple strategies side-by-side)

### v0.3 — Planned
- [ ] Risk parity (equal-risk-contribution) optimization
- [ ] Black-Litterman model
- [ ] Custom return priors
- [ ] Extended lookback with data caching

### v1.0 — Target
- [ ] Stable, versioned public API with deprecation policy
- [ ] Full Sphinx / MkDocs documentation site
- [ ] PyPI production release
- [ ] Docker image for the FastAPI service

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Implement changes with tests
4. Ensure `ruff check .`, `mypy src`, and `pytest -m "not network"` all pass
5. Open a pull request against `main`

Please ensure:
- All public functions have type annotations
- New features include unit tests
- Existing test coverage does not decrease
- No internal implementation details leak into the public API

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Disclaimer

This software is provided for **educational and research purposes only**. It does not constitute financial advice, investment recommendations, or guarantees of future performance. Users are solely responsible for their own investment decisions.

---

## Author

**Pratham Mishra**  
Computer Engineering Student · Quantitative Finance Enthusiast · Open Source Developer
