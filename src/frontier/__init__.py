"""
frontier — Stateless Vectorized Portfolio Optimization Engine.

Minimalist public API. Import directly from the top-level package:

    from frontier import optimize, fetch_data

For the FastAPI web server install the [server] extra:

    pip install frontier-quant[server]

then run:

    uvicorn frontier.api.main:app --reload
"""

from .core.optimizer import (
    optimize_portfolio as optimize,
    portfolio_performance,
)
from .adapters.yfinance_client import fetch_historical_returns as fetch_data

from importlib.metadata import version as _pkg_version, PackageNotFoundError as _PNF

try:
    __version__ = _pkg_version("frontier-quant")
except _PNF:
    # Package not yet installed (e.g. bare source checkout without pip install -e .)
    __version__ = "0.0.0+dev"
__author__ = "Pratham Mishra"
__license__ = "MIT"

__all__ = [
    # Clean public aliases
    "optimize",
    "fetch_data",
    # Full names (still importable for power users)
    "optimize_portfolio",
    "portfolio_performance",
    "fetch_historical_returns",
    # Package metadata
    "__version__",
    "__author__",
    "__license__",
]

# Also expose the full names so `from frontier import optimize_portfolio` still works
optimize_portfolio = optimize
fetch_historical_returns = fetch_data
