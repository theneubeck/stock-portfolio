Feature: Portfolio descriptive statistics
  As an investor
  I want to see min, max, median, and extreme-period statistics for my portfolio
  So that I can understand the full range of outcomes and key milestones

  Background:
    Given a portfolio with the following holdings for statistics:
      | symbol | shares | name                              |
      | GLD    | 50     | SPDR Gold Shares                  |
      | GSG    | 80     | iShares S&P GSCI Commodity ETF    |
      | ACWI   | 60     | iShares MSCI ACWI ETF             |
      | AGG    | 100    | iShares Core US Aggregate Bond ETF|
    And the benchmark is "ACWI"
    And the analysis period is max
    And the data interval is monthly

  Scenario: Per-holding price extremes
    When I fetch historical price data
    And I calculate per-holding statistics
    Then each holding should have a minimum price and its date
    And each holding should have a maximum price and its date
    And each holding should have a median price
    And the maximum price should be greater than or equal to the minimum price

  Scenario: Per-holding return distribution
    When I fetch historical price data
    And I calculate per-holding statistics
    Then each holding should have a best single-period return and its date
    And each holding should have a worst single-period return and its date
    And each holding should have a median periodic return
    And each holding should have a standard deviation of returns

  Scenario: Portfolio-level value extremes
    When I fetch historical price data
    And I calculate portfolio statistics
    Then the portfolio should have a peak value and its date
    And the portfolio should have a trough value and its date
    And the portfolio should have a current value
    And the peak value should be greater than or equal to the trough value

  Scenario: Portfolio-level return distribution
    When I fetch historical price data
    And I calculate portfolio statistics
    Then the portfolio should have a best single-period return and its date
    And the portfolio should have a worst single-period return and its date
    And the portfolio should have a median periodic return
    And the portfolio should have a mean periodic return
    And the portfolio should have positive and negative period counts

  Scenario: Portfolio statistics appear in the full report
    When I run the full analysis with statistics
    Then the report should contain a statistics section
    And the statistics section should include per-holding stats
    And the statistics section should include portfolio-level stats
