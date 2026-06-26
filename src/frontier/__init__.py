
"""
frontier — Stateless Vectorized Portfolio Optimization Engine.

Minimalist public API.

Core library:

    from frontier import optimize

Optional data adapter:

    from frontier import fetch_data

Requires:

    pip install frontier-quant[data]

FastAPI server:

    pip install frontier-quant[server]

Run:

    uvicorn frontier.api.main:app --reload
"""

from importlib.metadata import PackageNotFoundError as _PNF
from importlib.metadata import version as _pkg_version

from .core.optimizer import (
    optimize_portfolio,
    portfolio_performance,
)

# Clean public alias
optimize = optimize_portfolio


def fetch_data(*args, **kwargs):
    """
    Lazily import the Yahoo Finance adapter.

    This keeps frontier's core dependencies lightweight while allowing
    users to opt into market-data functionality via the [data] extra.
    """
    try:
        from .adapters.yfinance_client import fetch_historical_returns
    except ModuleNotFoundError as exc:
        raise ImportError(
            "The Yahoo Finance adapter requires the optional 'data' dependencies.\n\n"
            "Install them with:\n\n"
            "    pip install frontier-quant[data]"
        ) from exc

    return fetch_historical_returns(*args, **kwargs)


try:
    __version__ = _pkg_version("frontier-quant")
except _PNF:
    __version__ = "0.0.0+dev"

__author__ = "Pratham Mishra"
__license__ = "MIT"

__all__ = [
    "optimize",
    "optimize_portfolio",
    "portfolio_performance",
    "fetch_data",
    "__version__",
    "__author__",
    "__license__",
]
