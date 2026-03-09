Feature: Portfolio analysis with real market data
  As an investor
  I want to analyze a balanced portfolio of 4 asset classes against the world index
  So that I can understand my portfolio's performance, risk, and allocation

  Background:
    Given a portfolio with the following holdings:
      | symbol | shares | name                              |
      | GLD    | 50     | SPDR Gold Shares                  |
      | GSG    | 80     | iShares S&P GSCI Commodity ETF    |
      | ACWI   | 60     | iShares MSCI ACWI ETF             |
      | AGG    | 100    | iShares Core US Aggregate Bond ETF|
    And the benchmark is "ACWI"
    And the analysis period is max
    And the data interval is monthly

  Scenario: Fetch historical prices for all holdings and benchmark
    When I fetch historical price data
    Then I should have price data for each holding
    And I should have price data for the benchmark

  Scenario: Calculate individual holding returns
    When I fetch historical price data
    And I calculate individual returns
    Then each holding should have a total return percentage
    And each holding should have an annualized return

  Scenario: Calculate portfolio total value and weights
    When I fetch historical price data
    And I calculate the portfolio allocation
    Then each holding should have a current market value
    And each holding should have a weight as percentage of the portfolio
    And the weights should sum to 100 percent

  Scenario: Calculate portfolio risk metrics
    When I fetch historical price data
    And I calculate portfolio risk metrics
    Then the portfolio should have a volatility value
    And the portfolio should have a Sharpe ratio
    And the portfolio should have a maximum drawdown

  Scenario: Compare portfolio to the world index benchmark
    When I fetch historical price data
    And I compare the portfolio to the benchmark
    Then I should see the portfolio total return
    And I should see the benchmark total return
    And I should see the excess return over the benchmark

  Scenario: Generate a full analysis report
    When I run the full analysis
    Then the report should contain a summary section
    And the report should contain an allocation section
    And the report should contain a performance section
    And the report should contain a risk section
    And the report should contain a benchmark comparison section
