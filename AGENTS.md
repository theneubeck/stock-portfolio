# AGENTS.md — Portfolio Analyzer

## Project Overview

A Python-based portfolio analyzer that evaluates investment portfolios, calculates key metrics (returns, risk, allocation), and provides actionable insights. Built with a **Behaviour-Driven Development (BDD)** approach, working **outside-in** — every feature starts with a failing acceptance test before any production code is written.

---

## Tech Stack

| Concern | Tool |
| --------------- | ------------------------------------------- |
| Runtime | Python 3.12+ |
| Package manager | **uv** |
| Test framework | **pytest** + **pytest-bdd** (Gherkin `.feature` files) |
| Linting | **ruff** |
| Formatting | **ruff format** |
| Type checking | **mypy** (strict mode) |
| Task runner | **make** |

---

## Development Workflow — BDD, Outside-In

Every change follows this cycle:

### 1. Write a Gherkin Feature

Create (or extend) a `.feature` file under `tests/features/`.

```gherkin
Feature: Portfolio total value
  Scenario: Single holding
    Given a portfolio with the following holdings:
      | symbol | shares | price |
      | AAPL   | 10     | 150.0 |
    When I calculate the total value
    Then the total value should be 1500.0
```

### 2. Write the Step Definitions (Red)

Add step definitions in `tests/step_defs/` that reference the feature. Run `make tests` — the test **must fail** because no production code exists yet.

### 3. Write the Minimum Production Code (Green)

Implement just enough code in `src/portfolio_analyzer/` to make the failing test pass.

### 4. Refactor

Clean up the code while keeping all tests green. Run the full check suite:

```bash
make check   # runs format, lint, typecheck, tests
```

### 5. Repeat

Pick the next scenario or feature and start from step 1.

---

## Project Structure

```
portfolio/
├── AGENTS.md
├── Makefile
├── pyproject.toml
├── README.md
├── src/
│   └── portfolio_analyzer/
│       ├── __init__.py
│       ├── models.py          # Domain models (Holding, Portfolio)
│       ├── metrics.py         # Calculations (returns, risk, allocation)
│       └── analyzer.py        # High-level orchestration
├── tests/
│   ├── conftest.py
│   ├── features/              # Gherkin .feature files
│   │   └── portfolio_value.feature
│   └── step_defs/             # pytest-bdd step implementations
│       └── test_portfolio_value.py
└── examples/
    └── basic_usage.py
```

---

## Key Commands

| Command | What it does |
| -------------------- | --------------------------------------------- |
| `uv sync` | Install / sync all dependencies |
| `make format` | Auto-format with **ruff format** |
| `make lint` | Lint with **ruff check** (auto-fix enabled) |
| `make typecheck` | Run **mypy** in strict mode |
| `make tests` | Run **pytest** (BDD + unit tests) |
| `make check` | Run all of the above in sequence |

---

## Coding Conventions

### General

- All production code lives under `src/portfolio_analyzer/`.
- All tests live under `tests/`.
- Public functions and classes must have **docstrings**.
- Use **type hints** everywhere — mypy strict must pass.

### Testing

- **Acceptance tests first.** Every user-facing behaviour starts as a Gherkin scenario.
- **Unit tests welcome** for complex internal logic, but they complement — not replace — BDD scenarios.
- Test file names mirror step definition targets: `tests/step_defs/test_<feature>.py`.
- Use `conftest.py` for shared fixtures.
- Aim for **one assertion per scenario step** where possible.

### Style

- Follow **ruff** defaults (superset of PEP 8).
- Max line length: 99.
- Imports sorted by ruff (`isort` compatible).
- No unused imports, no unused variables.

### Git

- Commit messages: `<type>: <short summary>` (e.g., `feat: add portfolio total value calculation`).
- Types: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`.
- Keep commits atomic — one logical change per commit.

---

## Adding a New Feature — Checklist

1. [ ] Write a `.feature` file describing the behaviour.
2. [ ] Write step definitions — verify the test **fails**.
3. [ ] Implement production code — verify the test **passes**.
4. [ ] Refactor — all checks still pass (`make check`).
5. [ ] Update `README.md` / examples if user-facing behaviour changed.
6. [ ] Commit with a clear message.

---

### Review Process & What Reviewers Look For

- ✅ Checks pass (`make format`, `make lint`, `make typecheck`, `make tests`).
- ✅ Tests cover new behavior and edge cases.
- ✅ Code is readable, maintainable, and consistent with existing style.
- ✅ Public APIs and user-facing behavior changes are documented.
- ✅ Examples are updated if behavior changes.
- ✅ History is clean with a clear PR description.
