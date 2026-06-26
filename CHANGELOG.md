# Changelog

All notable changes to `frontier-quant` are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.2] — 2026-06-25

### Fixed — Critical (Release-Blocking)

#### BUG-01 — `frontier/api/main.py`: Eager import of `yfinance` adapter crashed server-only installs

`frontier/api/main.py` imported `fetch_historical_returns` at module level.
This caused `uvicorn frontier.api.main:app` to raise `ModuleNotFoundError: No module named 'yfinance'`
for any user who installed only `pip install frontier-quant[server]` — making **Scenario C
completely broken**.

**Fix:** The import is now deferred inside the `optimize_from_tickers()` handler body.
If `[data]` is not installed, the endpoint returns **HTTP 501** with a clear installation
instruction instead of crashing the server process.

#### BUG-02 — `frontier/adapters/yfinance_client.py`: Top-level optional imports

`import yfinance` and `import pandas` appeared at the top of the adapter module.
Any code path that touched the adapter — even just referencing it — would immediately
fail with `ModuleNotFoundError` on a core-only install.  This was the root cause of the
original production bug.

**Fix:** Both imports are now deferred to the first line of `fetch_historical_returns()`.
Importing the module is now always safe.  A clear `ImportError` with install instructions
is raised only when the function is actually called without `[data]` installed.

#### BUG-03 — `tests/test_api.py`: Module-level imports crashed pytest collection

`from frontier.api.main import app` and `client = TestClient(app)` at module level caused
the **entire test collection phase** to fail when `fastapi` or `yfinance` were absent —
not just those tests.

**Fix:** `pytest.importorskip("fastapi")` and `pytest.importorskip("yfinance")` are now
placed at the top of the file.  The module is skipped cleanly; the rest of the test suite
continues unaffected.

### Fixed — High Risk

#### RISK-01 — `frontier/core/optimizer.py`: Absolute import instead of relative import

`from frontier.exceptions import ConvergenceError` was an absolute import inconsistent with
the rest of the package.

**Fix:** Changed to `from ..exceptions import ConvergenceError` (relative import).

#### RISK-04 — `pyproject.toml`: `[all]` extra bundled dev tools into production install

`[all]` included `pytest`, `pytest-cov`, `ruff`, `mypy`, and `httpx` — developer-only
tools that should never be installed in production environments.

**Fix:** `[all]` now contains only the production runtime extras (`data` + `server`).
Developer tools remain exclusively in `[dev]`.  `pandas-stubs` and `scipy-stubs` (previously
missing from `[dev]`) have been added.

### Removed

#### `requirements.txt` — Deleted

The file incorrectly listed all optional dependencies (`fastapi`, `uvicorn`, `yfinance`)
as mandatory, contradicting `pyproject.toml` and misleading contributors and CI pipelines.

**Replacement:** `requirements-dev.txt` — a single-line `-e .[all,dev]` file that is
explicitly scoped to local development only.

### Added

#### `tests/test_isolation.py` — Dependency isolation regression tests

A new test module that simulates environments missing optional extras using Python's
import machinery.  Prevents the v0.1.2 bug class from ever silently returning.

Covers:
- Adapter module imports without yfinance/pandas
- API module imports without yfinance (server-only install)
- Core package (`import frontier`) without any optional extras
- Core engine isolation (`frontier.core` — stdlib + numpy + scipy only)
- Models isolation (`frontier.models` — pydantic only)
- Public API surface contract (`frontier.__all__`)

#### `requirements-dev.txt`

Single-line developer convenience file: `-e .[all,dev]`.

#### `CHANGELOG.md`

This file.

### Packaging

- Version bumped: `0.1.1` → `0.1.2`
- Added `Changelog` URL to `[project.urls]`

---

## [0.1.1] — 2026-06-20

### Added

- Initial public release on PyPI
- Core portfolio optimisation engine (`frontier.core.optimizer`)
- Yahoo Finance data adapter (`frontier.adapters.yfinance_client`) — `[data]` extra
- FastAPI HTTP server (`frontier.api.main`) — `[server]` extra
- Pydantic request/response schemas (`frontier.models.schemas`)
- Typed exception hierarchy (`frontier.exceptions`)
- `py.typed` marker for PEP 561 compliance

### Known Issues (fixed in 0.1.2)

- BUG-01: `[server]` extra failed if `[data]` was not also installed
- BUG-02: `yfinance_client.py` had eager top-level optional imports
- BUG-03: `test_api.py` crashed pytest collection without `[server]`+`[data]`
