"""
tests/test_isolation.py — Regression tests for dependency isolation.

These tests verify that the class of bugs fixed in v0.1.2 can never silently
return to the codebase:

    BUG-01: frontier/api/main.py eagerly imported yfinance at module level,
            breaking `pip install frontier-quant[server]`.

    BUG-02: frontier/adapters/yfinance_client.py had top-level `import yfinance`
            and `import pandas`, causing ImportError on core-only installs.

    BUG-03: tests/test_api.py crashed pytest collection without [server]+[data].

These tests use Python's import machinery to simulate environments where
optional extras are absent — WITHOUT actually uninstalling any packages.

All tests in this module run fully offline.  No network, no subprocess.
"""

import builtins
import importlib
import sys
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _block_imports(*blocked: str):
    """
    Context manager that raises ModuleNotFoundError for the named modules,
    simulating a clean install without those optional extras.
    """
    real_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        top = name.split(".")[0]
        if top in blocked:
            raise ModuleNotFoundError(
                f"[test_isolation] Simulated missing package: {name!r}"
            )
        return real_import(name, *args, **kwargs)

    return patch("builtins.__import__", side_effect=_fake_import)


def _fresh_import(module_path: str):
    """
    Remove a module (and any already-cached submodules) from sys.modules,
    then re-import it fresh.  Allows testing module-level import behaviour.
    """
    to_remove = [k for k in sys.modules if k == module_path or k.startswith(module_path + ".")]
    for key in to_remove:
        del sys.modules[key]
    return importlib.import_module(module_path)


# ===========================================================================
# BUG-02 Regression — yfinance_client module import never fails on core install
# ===========================================================================

class TestAdapterModuleImport:
    """
    Verify that frontier.adapters.yfinance_client can be imported without
    yfinance or pandas installed.
    """

    def test_yfinance_client_module_imports_without_yfinance(self):
        """
        Regression for BUG-02.
        Importing the adapter module must succeed even when yfinance is absent.
        """
        with _block_imports("yfinance", "pandas"):
            # Remove any cached version first
            _keys = [k for k in sys.modules if "yfinance_client" in k]
            for k in _keys:
                del sys.modules[k]
            # This must NOT raise
            import frontier.adapters.yfinance_client  # noqa: F401

    def test_fetch_historical_returns_raises_import_error_without_yfinance(self):
        """
        Calling fetch_historical_returns without yfinance installed must raise
        ImportError with a clear pip install instruction.
        """
        from frontier.adapters.yfinance_client import fetch_historical_returns

        with _block_imports("yfinance"):
            with pytest.raises(ImportError) as exc_info:
                fetch_historical_returns(["AAPL", "MSFT"])

        assert "pip install frontier-quant[data]" in str(exc_info.value)

    def test_fetch_historical_returns_raises_import_error_without_pandas(self):
        """
        Calling fetch_historical_returns without pandas installed must raise
        ImportError with a clear pip install instruction.
        """
        from frontier.adapters.yfinance_client import fetch_historical_returns

        with _block_imports("pandas"):
            with pytest.raises(ImportError) as exc_info:
                fetch_historical_returns(["AAPL", "MSFT"])

        assert "pip install frontier-quant[data]" in str(exc_info.value)

    def test_fetch_historical_returns_raises_value_error_on_empty_tickers(self):
        """
        Empty ticker list must raise ValueError BEFORE any optional import attempt.
        This ensures the guard runs first.
        """
        from frontier.adapters.yfinance_client import fetch_historical_returns

        with pytest.raises(ValueError, match="cannot be empty"):
            fetch_historical_returns([])


# ===========================================================================
# BUG-01 Regression — api/main.py never imports yfinance at module level
# ===========================================================================

class TestAPIModuleImport:
    """
    Verify that frontier.api.main can be imported (the FastAPI app created)
    without the [data] extra installed.
    """

    def test_api_main_imports_without_yfinance(self):
        """
        Regression for BUG-01.
        frontier.api.main must be importable with only [server] extra installed
        (i.e., without yfinance or pandas).
        """
        pytest.importorskip("fastapi", reason="requires pip install frontier-quant[server]")

        # Evict cached module so we get a fresh import
        _keys = [k for k in sys.modules if "frontier.api" in k]
        for k in _keys:
            del sys.modules[k]

        with _block_imports("yfinance", "pandas"):
            # This must NOT raise even though yfinance is "missing"
            import frontier.api.main  # noqa: F401

    def test_api_app_object_exists_without_yfinance(self):
        """
        The FastAPI `app` object must be accessible without the data extra.
        """
        pytest.importorskip("fastapi", reason="requires pip install frontier-quant[server]")

        _keys = [k for k in sys.modules if "frontier.api" in k]
        for k in _keys:
            del sys.modules[k]

        with _block_imports("yfinance", "pandas"):
            from frontier.api.main import app  # noqa: F401
            assert app is not None


# ===========================================================================
# Core package isolation — import frontier without any optional extras
# ===========================================================================

class TestCorePackageIsolation:
    """
    Verify that `import frontier` succeeds with only core dependencies:
    numpy, scipy, pydantic.

    No yfinance, pandas, fastapi, or uvicorn should be required.
    """

    def test_import_frontier_without_optional_extras(self):
        """
        Regression for original production bug.
        `import frontier` must never import optional dependencies.
        """
        with _block_imports("yfinance", "pandas", "fastapi", "uvicorn"):
            # Evict cached frontier modules
            _keys = [k for k in sys.modules if k.startswith("frontier")]
            for k in _keys:
                del sys.modules[k]
            # Must not raise
            import frontier  # noqa: F401

    def test_optimize_available_without_optional_extras(self):
        """
        from frontier import optimize must work on a core-only install.
        """
        with _block_imports("yfinance", "pandas", "fastapi", "uvicorn"):
            _keys = [k for k in sys.modules if k.startswith("frontier")]
            for k in _keys:
                del sys.modules[k]
            from frontier import optimize  # noqa: F401
            assert callable(optimize)

    def test_fetch_data_callable_without_optional_extras(self):
        """
        frontier.fetch_data must be callable (a function) even without [data].
        It must only raise ImportError when actually *called*.
        """
        with _block_imports("yfinance", "pandas", "fastapi", "uvicorn"):
            _keys = [k for k in sys.modules if k.startswith("frontier")]
            for k in _keys:
                del sys.modules[k]
            import frontier
            assert callable(frontier.fetch_data)

    def test_fetch_data_raises_import_error_when_called_without_data_extra(self):
        """
        Calling frontier.fetch_data() without [data] installed must raise
        ImportError with a clear pip install instruction — not a bare
        ModuleNotFoundError or an AttributeError.
        """
        from frontier import fetch_data

        with _block_imports("yfinance"):
            with pytest.raises(ImportError) as exc_info:
                fetch_data(["AAPL", "MSFT"])

        error_text = str(exc_info.value)
        assert "pip install frontier-quant[data]" in error_text

    def test_version_accessible_without_optional_extras(self):
        """frontier.__version__ must be readable without optional extras."""
        with _block_imports("yfinance", "pandas", "fastapi", "uvicorn"):
            _keys = [k for k in sys.modules if k.startswith("frontier")]
            for k in _keys:
                del sys.modules[k]
            import frontier
            assert isinstance(frontier.__version__, str)
            assert len(frontier.__version__) > 0


# ===========================================================================
# Core engine isolation — frontier.core must not import optional deps
# ===========================================================================

class TestCoreEngineIsolation:
    """
    frontier.core must depend ONLY on Python stdlib + numpy + scipy.
    """

    def test_core_optimizer_imports_without_optional_extras(self):
        """frontier.core.optimizer must import cleanly without pandas/yfinance/fastapi."""
        with _block_imports("yfinance", "pandas", "fastapi", "uvicorn"):
            _keys = [k for k in sys.modules if "frontier.core" in k]
            for k in _keys:
                del sys.modules[k]
            import frontier.core.optimizer  # noqa: F401

    def test_optimize_portfolio_callable_without_optional_extras(self):
        """optimize_portfolio must be callable without optional extras."""
        with _block_imports("yfinance", "pandas", "fastapi", "uvicorn"):
            _keys = [k for k in sys.modules if "frontier.core" in k]
            for k in _keys:
                del sys.modules[k]
            from frontier.core.optimizer import optimize_portfolio
            assert callable(optimize_portfolio)


# ===========================================================================
# Models isolation — frontier.models must not import optional deps
# ===========================================================================

class TestModelsIsolation:
    """frontier.models must depend only on pydantic (core dep)."""

    def test_models_import_without_optional_extras(self):
        """frontier.models.schemas must import cleanly without optional extras."""
        with _block_imports("yfinance", "pandas", "fastapi", "uvicorn"):
            _keys = [k for k in sys.modules if "frontier.models" in k]
            for k in _keys:
                del sys.modules[k]
            import frontier.models.schemas  # noqa: F401


# ===========================================================================
# __all__ contract — public API surface is stable
# ===========================================================================

class TestPublicAPI:
    """Verify the public API exports are all present and have correct types."""

    def test_all_exports_present(self):
        """Every name in frontier.__all__ must be importable from frontier."""
        import frontier
        for name in frontier.__all__:
            assert hasattr(frontier, name), f"frontier.__all__ includes {name!r} but it's missing"

    def test_optimize_is_callable(self):
        import frontier
        assert callable(frontier.optimize)

    def test_optimize_portfolio_is_callable(self):
        import frontier
        assert callable(frontier.optimize_portfolio)

    def test_portfolio_performance_is_callable(self):
        import frontier
        assert callable(frontier.portfolio_performance)

    def test_fetch_data_is_callable(self):
        import frontier
        assert callable(frontier.fetch_data)
