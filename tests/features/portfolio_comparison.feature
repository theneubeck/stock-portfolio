Feature: Compare multiple portfolio strategies
  As an investor
  I want to compare different portfolio allocations side by side
  So that I can choose the best strategy for my goals

  Background:
    Given the following portfolio strategies:
      | name             | GLD | GSG | ACWI | AGG |
      | Equal Weight     | 25  | 25  | 25   | 25  |
      | Heavy Gold       | 50  | 10  | 20   | 20  |
      | Stocks & Bonds   | 0   | 0   | 60   | 40  |
      | All Weather      | 30  | 15  | 30   | 25  |
    And the monthly investment is 100 USD for all strategies
    And rebalancing occurs every 6 months for all strategies
    And the benchmark is "ACWI"
    And the comparison period is max
    And the comparison interval is monthly

  Scenario: Run all strategies and collect results
    When I run the portfolio comparison
    Then I should have results for 4 strategies
    And each strategy should have a final value
    And each strategy should have a total return

  Scenario: Rank strategies by total return
    When I run the portfolio comparison
    Then I should see strategies ranked by total return
    And the best performing strategy should be listed first
    And the worst performing strategy should be listed last

  Scenario: Compare risk across strategies
    When I run the portfolio comparison
    Then each strategy should have a volatility measure
    And each strategy should have a max drawdown
    And each strategy should have a Sharpe ratio

  Scenario: Compare strategies against the benchmark
    When I run the portfolio comparison
    Then each strategy should show excess return vs the benchmark
    And I should see which strategies beat the benchmark
    And I should see which strategies underperformed the benchmark

  Scenario: Generate a comparison report
    When I run the portfolio comparison
    Then the comparison report should list all strategy names
    And the comparison report should show a side-by-side summary table
    And the comparison report should identify the best and worst strategies
