Frontier API Documentation

Frontier is a blazing-fast, stateless Mean-Variance portfolio optimization engine.

Built with a strict separation of concerns, Frontier abstracts the heavy lifting of quantitative finance into an easy-to-use Python library and a deployable FastAPI microservice. Whether you are a Quant passing in proprietary Bloomberg data arrays, or a Web Developer who just wants to pass a list of stock tickers to build a dashboard, Frontier handles the math.

📦 Installation

Frontier is distributed via PyPI. You can install it in two ways depending on your use case:

1. As a Pure Quantitative Library (For Jupyter / Data Science)

pip install frontier-api


2. As a Web Service (Includes FastAPI & Uvicorn)

pip install frontier-api[server]


🧠 Core Architecture

Frontier is built on two decoupled pillars:

The Math Engine (core.optimizer): Pure NumPy/SciPy linear algebra. It knows nothing about the internet, stock tickers, or Yahoo Finance. It only computes matrices.

The Data Adapters (adapters): Helper functions that reach out to external sources (like yfinance), clean the data, handle missing IPO rows, and format the arrays for the Math Engine.

🐍 Python Library Guide

If you are using Frontier inside your own Python application, you interact with the Python modules directly.

1. Using the Data Adapter

The yfinance adapter accepts a list of tickers and safely handles missing data to ensure matrix dimensions match perfectly.

from frontier_api.adapters.yfinance_client import fetch_historical_returns

# Fetch 3 years of daily returns
returns_dict = fetch_historical_returns(
    tickers=["AAPL", "MSFT", "GOOG"], 
    lookback_years=3
)


2. Using the Math Engine

Pass your dictionary of returns into the optimizer. You can use the adapter's output, or provide your own proprietary data.

from frontier_api.core.optimizer import optimize_portfolio

# The risk-free rate defaults to 0.04 (4%)
result = optimize_portfolio(returns_dict, risk_free_rate=0.04)

print("Optimal Weights:", result["optimal_portfolio"]["weights"])
print("Max Sharpe Ratio:", result["optimal_portfolio"]["sharpe_ratio"])


🌐 REST API Guide

If you installed with [server], you can instantly launch Frontier as a local REST API.

Start the server:

uvicorn frontier_api.api.main:app --reload


Once running, visit http://localhost:8000/docs for the interactive Swagger UI.

Endpoint 1: /v1/optimize (Pure Math)

Designed for enterprise integration. Send your own calculated return arrays. No internet calls are made by the server.

Request Payload:

{
  "returns": {
    "AAPL": [0.012, -0.005, 0.021],
    "MSFT": [0.008, -0.001, 0.015]
  },
  "risk_free_rate": 0.04
}


Endpoint 2: /v1/optimize_from_tickers (Convenience)

Designed for frontend developers. Send a list of tickers, and the API will internally fetch the market data, optimize it, and return the weights.

Request Payload:

{
  "tickers": ["AAPL", "MSFT", "GOOG"],
  "lookback_years": 3,
  "risk_free_rate": 0.04
}


Standard API Response

Both endpoints return the exact same JSON structure, allowing seamless plotting of the Efficient Frontier on frontend dashboards.

{
  "status": "success",
  "metadata": {
    "data_source": "Yahoo Finance (yfinance)",
    "assets_analyzed": ["AAPL", "GOOG", "MSFT"],
    "trading_days_per_asset": 754
  },
  "optimal_portfolio": {
    "sharpe_ratio": 1.25,
    "expected_annual_return": 0.38,
    "annual_volatility": 0.27,
    "weights": {
      "AAPL": 0.12,
      "GOOG": 0.88,
      "MSFT": 0.0
    }
  },
  "frontier_curve": [
    { "volatility": 0.21, "return_rate": 0.15 },
    { "volatility": 0.23, "return_rate": 0.22 }
    // ... exactly 20 points mapped
  ]
}


🧮 Mathematical Notes

Optimization Solver: Uses SciPy's Sequential Least Squares Programming (SLSQP).

Constraints: Long-only (no short selling). Weights are strictly bound between 0.0 and 1.0 and must sum exactly to 1.0.

Annualization: Daily returns and covariance matrices are multiplied by 252 (standard trading days per year).

Efficient Frontier: The frontier_curve array returns exactly 20 optimized coordinates dynamically mapped between the lowest and highest expected returns of the provided assets.