# Frontier

A Python library for portfolio optimization, efficient frontier analysis, and quantitative asset allocation.

Frontier API provides tools for retrieving historical market data, computing asset return statistics, and generating optimized portfolios using Modern Portfolio Theory (MPT). The project is designed to be used both as a standalone Python package and as the computational engine behind portfolio optimization services and applications.

---

## Features

* Historical market data retrieval
* Portfolio return and risk analysis
* Mean-variance optimization
* Efficient frontier construction
* Portfolio weight optimization
* Modular architecture for extension and customization
* FastAPI integration support
* Type-safe data models
* Comprehensive test suite

---

## Motivation

Constructing an investment portfolio involves balancing expected return against risk. While many retail tools provide basic allocation recommendations, quantitative portfolio construction often requires a reproducible and programmable workflow.

Frontier API aims to provide:

* A clean Python interface for portfolio optimization
* Transparent optimization logic
* Extensible architecture for future quantitative models
* Open-source accessibility for developers, students, researchers, and investors

---

## Project Architecture

```text
frontier-api/
│
├── pyproject.toml
├── README.md
├── tests/
│
└── src/
    └── frontier/
        ├── adapters/
        │   └── yfinance_client.py
        │
        ├── api/
        │   └── main.py
        │
        ├── core/
        │   └── optimizer.py
        │
        ├── models/
        │   └── schemas.py
        │
        └── __init__.py
```

### Package Structure

| Module   | Responsibility                      |
| -------- | ----------------------------------- |
| adapters | External data source integrations   |
| core     | Portfolio optimization algorithms   |
| models   | Data schemas and validation         |
| api      | FastAPI endpoints and service layer |
| tests    | Unit and integration tests          |

---

## Installation

### Requirements

* Python 3.10+
* pip

### Install from Source

```bash
git clone https://github.com/your-username/frontier-api.git
cd frontier-api

pip install -e .
```

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

---

## Quick Start

### Import the Optimizer

```python
from frontier import optimize
```

### Fetch Historical Data

```python
from frontier import fetch_data

returns = fetch_data(
    tickers=["AAPL", "MSFT", "GOOGL"],
    lookback_years=5
)
```

### Optimize Portfolio

```python
from frontier import optimize

weights = optimize(returns)

print(weights)
```

---

## Example Workflow

```python
from frontier import fetch_data, optimize

tickers = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN"
]

returns = fetch_data(
    tickers=tickers,
    lookback_years=5
)

portfolio = optimize(returns)

print(portfolio)
```

---

## Optimization Methodology

The current implementation is based on Modern Portfolio Theory (MPT).

The optimization process generally includes:

1. Historical price retrieval
2. Return calculation
3. Covariance matrix estimation
4. Portfolio risk calculation
5. Expected return estimation
6. Weight optimization
7. Efficient frontier generation

Future versions may support:

* Black-Litterman models
* Risk parity portfolios
* Hierarchical Risk Parity (HRP)
* CVaR optimization
* Monte Carlo simulation
* Factor investing models

---

## API Usage

The package can also be exposed through FastAPI.

Run the server:

```bash
uvicorn frontier.api.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

Interactive Swagger documentation will be available automatically.

---

## Testing

Run the complete test suite:

```bash
pytest
```

Run a specific test:

```bash
pytest tests/test_optimizer.py
```

Generate coverage:

```bash
pytest --cov=frontier
```

---

## Development

Install the package in editable mode:

```bash
pip install -e .
```

This ensures local code changes are immediately reflected without reinstalling the package.

---

## Roadmap

### Version 0.1

* Historical market data retrieval
* Portfolio optimization engine
* FastAPI integration
* Unit testing

### Version 0.2

* Efficient frontier visualization
* Sharpe ratio maximization
* Portfolio analytics

### Version 0.3

* Risk parity optimization
* Black-Litterman model
* Portfolio backtesting

### Version 1.0

* Stable public API
* Comprehensive documentation
* PyPI distribution
* Production-ready architecture

---

## Contributing

Contributions are welcome.

To contribute:

1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Add or update tests
5. Submit a pull request

Please ensure:

* Code is fully tested
* Public APIs are documented
* Type hints are used where appropriate
* Existing functionality remains backward compatible

---

## License

This project is licensed under the MIT License.

See the LICENSE file for details.

---

## Disclaimer

This software is provided for educational and research purposes only.

The project does not provide financial advice, investment recommendations, or guarantees regarding future performance. Users are responsible for conducting their own due diligence before making investment decisions.

---

## Author

Pratham Mishra

Computer Engineering Student • Quantitative Finance Enthusiast • Open Source Developer
