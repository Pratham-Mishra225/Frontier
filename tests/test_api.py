"""
tests/test_api.py — FastAPI endpoint tests using TestClient.

All tests in this module run fully offline (no network calls).
Live yfinance calls are replaced with unittest.mock.patch.

This module requires both the [server] and [data] extras.
If either is absent, the entire module is skipped cleanly at
collection time — the rest of the test suite continues unaffected.

Coverage:
  GET  /health                         — status, schema
  POST /v1/optimize                    — happy path, invalid payloads, convergence failure
  POST /v1/optimize_from_tickers       — mocked happy path, missing field
"""
import pytest

# ---------------------------------------------------------------------------
# Guard — skip the entire module if optional server/data deps are absent.
# pytest.importorskip() will emit a clear SKIP reason and never raise an
# ImportError that would crash collection for the rest of the test suite.
# ---------------------------------------------------------------------------
pytest.importorskip(
    "fastapi",
    reason="API tests require pip install frontier-quant[server]",
)
pytest.importorskip(
    "yfinance",
    reason="API tests require pip install frontier-quant[data]",
)

from unittest.mock import patch  # noqa: E402 — intentionally after importorskip
from fastapi.testclient import TestClient  # noqa: E402

from frontier.api.main import app  # noqa: E402

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

VALID_RETURNS = {
    "AAPL": [0.010,  0.005, -0.002,  0.015,  0.008],
    "MSFT": [0.008,  0.010,  0.000, -0.005,  0.012],
    "GOOG": [-0.010, 0.020,  0.010, -0.015,  0.005],
}

# A minimal dict that satisfies the OptimizeResponse model when returned by a
# mocked optimizer (status / metadata receive their Pydantic defaults).
MOCK_OPTIMIZER_RESULT = {
    "optimal_portfolio": {
        "sharpe_ratio": 1.25,
        "expected_annual_return": 0.38,
        "annual_volatility": 0.27,
        "weights": {"AAPL": 0.12, "GOOG": 0.88, "MSFT": 0.0},
    },
    "frontier_curve": [
        {"volatility": 0.21, "return_rate": 0.15},
        {"volatility": 0.23, "return_rate": 0.22},
    ],
}


# ===========================================================================
# GET /health
# ===========================================================================

def test_health_returns_200():
    """Health endpoint must respond with HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_contains_status_field():
    """Health response body must include a 'status' field."""
    response = client.get("/health")
    assert "status" in response.json()


def test_health_response_contains_service_field():
    """Health response body must include a 'service' field."""
    response = client.get("/health")
    assert "service" in response.json()


def test_health_status_is_active():
    """Health endpoint must report status='active'."""
    response = client.get("/health")
    assert response.json()["status"] == "active"


# ===========================================================================
# POST /v1/optimize — happy path
# ===========================================================================

def test_optimize_valid_payload_returns_200():
    """Valid returns payload must produce HTTP 200."""
    response = client.post(
        "/v1/optimize",
        json={"returns": VALID_RETURNS, "risk_free_rate": 0.04},
    )
    assert response.status_code == 200


def test_optimize_response_has_optimal_portfolio():
    """Successful response must contain the 'optimal_portfolio' key."""
    response = client.post("/v1/optimize", json={"returns": VALID_RETURNS})
    assert "optimal_portfolio" in response.json()


def test_optimize_response_has_frontier_curve():
    """Successful response must contain the 'frontier_curve' key."""
    response = client.post("/v1/optimize", json={"returns": VALID_RETURNS})
    assert "frontier_curve" in response.json()


def test_optimize_response_has_status_field():
    """Successful response must contain the 'status' field (default: 'success')."""
    response = client.post("/v1/optimize", json={"returns": VALID_RETURNS})
    assert response.json().get("status") == "success"


def test_optimize_weights_sum_to_one():
    """Response weights must sum to approximately 1.0 (long-only constraint)."""
    response = client.post("/v1/optimize", json={"returns": VALID_RETURNS})
    weights = response.json()["optimal_portfolio"]["weights"]
    assert round(sum(weights.values()), 2) == 1.0


def test_optimize_all_weights_non_negative():
    """No weight in the response may be negative (long-only portfolio)."""
    response = client.post("/v1/optimize", json={"returns": VALID_RETURNS})
    weights = response.json()["optimal_portfolio"]["weights"]
    for ticker, w in weights.items():
        assert w >= 0.0, f"Negative weight for {ticker}: {w}"


def test_optimize_default_risk_free_rate_accepted():
    """Omitting risk_free_rate must still return 200 (default=0.04)."""
    response = client.post("/v1/optimize", json={"returns": VALID_RETURNS})
    assert response.status_code == 200


# ===========================================================================
# POST /v1/optimize — invalid / malformed payloads
# ===========================================================================

def test_optimize_single_asset_returns_400():
    """Single-asset input must be rejected with HTTP 400."""
    response = client.post(
        "/v1/optimize",
        json={"returns": {"AAPL": [0.01, 0.02, 0.03]}},
    )
    assert response.status_code == 400


def test_optimize_mismatched_series_lengths_returns_400():
    """Return series with different observation counts must return HTTP 400."""
    response = client.post(
        "/v1/optimize",
        json={
            "returns": {
                "AAPL": [0.01, 0.02, 0.03],
                "MSFT": [0.01, 0.02],
            }
        },
    )
    assert response.status_code == 400


def test_optimize_empty_returns_dict_returns_400():
    """An empty returns dictionary must return HTTP 400."""
    response = client.post(
        "/v1/optimize",
        json={"returns": {}},
    )
    assert response.status_code == 400


def test_optimize_missing_returns_field_returns_422():
    """Omitting the required 'returns' field must return HTTP 422 (schema error)."""
    response = client.post(
        "/v1/optimize",
        json={"risk_free_rate": 0.04},
    )
    assert response.status_code == 422


def test_optimize_malformed_json_returns_422():
    """Non-JSON body must return HTTP 422."""
    response = client.post(
        "/v1/optimize",
        content=b"this is not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_optimize_insufficient_observations_returns_400():
    """Series with a single observation must return HTTP 400."""
    response = client.post(
        "/v1/optimize",
        json={"returns": {"AAPL": [0.01], "MSFT": [0.02]}},
    )
    assert response.status_code == 400


# ===========================================================================
# POST /v1/optimize — convergence failure path (mocked, offline)
# ===========================================================================

def test_optimize_convergence_failure_returns_400():
    """A ConvergenceError from the optimizer must map to HTTP 400."""
    from frontier.exceptions import ConvergenceError

    with patch("frontier.api.main.optimize_portfolio") as mock_opt:
        mock_opt.side_effect = ConvergenceError("SLSQP iteration limit exceeded.")
        response = client.post("/v1/optimize", json={"returns": VALID_RETURNS})

    assert response.status_code == 400


def test_optimize_convergence_failure_detail_is_present():
    """The 400 error response must contain a human-readable 'detail' field."""
    from frontier.exceptions import ConvergenceError

    with patch("frontier.api.main.optimize_portfolio") as mock_opt:
        mock_opt.side_effect = ConvergenceError("SLSQP iteration limit exceeded.")
        response = client.post("/v1/optimize", json={"returns": VALID_RETURNS})

    data = response.json()
    assert "detail" in data
    assert len(data["detail"]) > 0


def test_optimize_convergence_failure_no_traceback_leaked():
    """The error response body must not contain a Python traceback."""
    from frontier.exceptions import ConvergenceError

    with patch("frontier.api.main.optimize_portfolio") as mock_opt:
        mock_opt.side_effect = ConvergenceError("SLSQP iteration limit exceeded.")
        response = client.post("/v1/optimize", json={"returns": VALID_RETURNS})

    body = response.text
    assert "Traceback" not in body
    assert 'File "' not in body


# ===========================================================================
# POST /v1/optimize_from_tickers — mocked (offline)
# ===========================================================================

def test_optimize_from_tickers_mocked_returns_200():
    """
    With yfinance and the optimizer both mocked, the tickers endpoint must
    return HTTP 200 — confirming the routing and response serialisation work.
    """
    with (
        patch("frontier.adapters.yfinance_client.fetch_historical_returns") as mock_fetch,
        patch("frontier.api.main.optimize_portfolio") as mock_opt,
    ):
        mock_fetch.return_value = VALID_RETURNS
        mock_opt.return_value = MOCK_OPTIMIZER_RESULT

        response = client.post(
            "/v1/optimize_from_tickers",
            json={"tickers": ["AAPL", "MSFT", "GOOG"], "lookback_years": 1},
        )

    assert response.status_code == 200


def test_optimize_from_tickers_mocked_response_has_optimal_portfolio():
    """Mocked tickers endpoint must return an 'optimal_portfolio' key."""
    with (
        patch("frontier.adapters.yfinance_client.fetch_historical_returns") as mock_fetch,
        patch("frontier.api.main.optimize_portfolio") as mock_opt,
    ):
        mock_fetch.return_value = VALID_RETURNS
        mock_opt.return_value = MOCK_OPTIMIZER_RESULT

        response = client.post(
            "/v1/optimize_from_tickers",
            json={"tickers": ["AAPL", "MSFT", "GOOG"], "lookback_years": 1},
        )

    assert "optimal_portfolio" in response.json()


def test_optimize_from_tickers_missing_tickers_field_returns_422():
    """Omitting the required 'tickers' field must return HTTP 422."""
    response = client.post(
        "/v1/optimize_from_tickers",
        json={"lookback_years": 1},
    )
    assert response.status_code == 422


def test_optimize_from_tickers_adapter_error_returns_400():
    """A ValueError from the data adapter must map to HTTP 400."""
    with patch("frontier.adapters.yfinance_client.fetch_historical_returns") as mock_fetch:
        mock_fetch.side_effect = ValueError("No data returned for ticker XYZ.")
        response = client.post(
            "/v1/optimize_from_tickers",
            json={"tickers": ["AAPL", "MSFT"], "lookback_years": 1},
        )

    assert response.status_code == 400


def test_optimize_from_tickers_network_error_returns_502():
    """A RuntimeError from yfinance (connection failure) must map to HTTP 502."""
    with patch("frontier.adapters.yfinance_client.fetch_historical_returns") as mock_fetch:
        mock_fetch.side_effect = RuntimeError("Failed to connect to Yahoo Finance.")
        response = client.post(
            "/v1/optimize_from_tickers",
            json={"tickers": ["AAPL", "MSFT"], "lookback_years": 1},
        )

    assert response.status_code == 502


# ===========================================================================
# Regression — data adapter missing (server-only install simulation)
# ===========================================================================

def test_optimize_from_tickers_returns_501_when_data_extra_missing():
    """
    Regression test for BUG-01.

    If the [data] extra is not installed, /v1/optimize_from_tickers must
    return HTTP 501 with a clear installation instruction — not crash the
    server process at startup.

    We simulate the missing-extra scenario by setting the adapter module to
    None in sys.modules, which causes any `from ... import` of that module
    to raise ModuleNotFoundError — exactly what happens on a [server]-only install.
    """
    import sys

    # Setting a module to None in sys.modules makes any subsequent
    # `import frontier.adapters.yfinance_client` raise ModuleNotFoundError.
    with patch.dict(
        sys.modules,
        {"frontier.adapters.yfinance_client": None},  # type: ignore[dict-item]
    ):
        response = client.post(
            "/v1/optimize_from_tickers",
            json={"tickers": ["AAPL", "MSFT"], "lookback_years": 1},
        )

    assert response.status_code == 501
    assert "pip install frontier-quant[data]" in response.json()["detail"]


# ===========================================================================
# Version availability
# ===========================================================================

def test_frontier_version_is_available():
    """frontier.__version__ must be a non-empty string."""
    import frontier
    assert isinstance(frontier.__version__, str)
    assert len(frontier.__version__) > 0


def test_api_version_matches_package_version():
    """The FastAPI app version must match the package __version__."""
    import frontier
    assert app.version == frontier.__version__
