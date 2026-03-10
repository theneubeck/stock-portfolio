# ──────────────────────────────────────────────
# Portfolio Analyzer — Makefile
# ──────────────────────────────────────────────

.PHONY: sync
sync:
	uv sync --all-extras --group dev

# ── Formatting ────────────────────────────────

.PHONY: format
format:
	uv run ruff format
	uv run ruff check --fix

.PHONY: format-check
format-check:
	uv run ruff format --check

# ── Linting ───────────────────────────────────

.PHONY: lint
lint:
	uv run ruff check

# ── Type checking ─────────────────────────────

.PHONY: typecheck
typecheck:
	uv run mypy .

# ── Testing ───────────────────────────────────

.PHONY: tests
tests:
	uv run pytest || test $$? -eq 5  # exit 5 = no tests collected (OK during bootstrap)

.PHONY: coverage
coverage:
	uv run coverage run -m pytest
	uv run coverage xml -o coverage.xml
	uv run coverage report -m --fail-under=85

# ── Web server ────────────────────────────────

.PHONY: serve
serve:
	uv run uvicorn portfolio_analyzer.web:app --reload --port 8000

# ── All checks (CI gate) ─────────────────────

.PHONY: check
check: format-check lint typecheck tests
