Feature: Dollar-cost averaging with periodic rebalancing
  As a long-term investor
  I want to invest a fixed amount each month and rebalance every 6 months
  So that I can see how disciplined investing grows over time

  Background:
    Given a DCA portfolio with the following holdings:
      | symbol | name                              | target_weight |
      | GLD    | SPDR Gold Shares                  | 25            |
      | GSG    | iShares S&P GSCI Commodity ETF    | 25            |
      | ACWI   | iShares MSCI ACWI ETF             | 25            |
      | AGG    | iShares Core US Aggregate Bond ETF| 25            |
    And the monthly investment is 100 USD
    And rebalancing occurs every 6 months
    And the benchmark is "ACWI"
    And the analysis period is max
    And the data interval is monthly

  Scenario: Simulate monthly DCA investments
    When I run the DCA simulation
    Then the total amount invested should be positive
    And the final portfolio value should be positive
    And the number of investment periods should match the price history length

  Scenario: Rebalancing restores target weights
    When I run the DCA simulation
    Then rebalancing should have occurred at least once
    And after each rebalance the weights should be within 1 percent of targets

  Scenario: Track portfolio value over time
    When I run the DCA simulation
    Then I should have a time series of portfolio values
    And the time series should start near the first monthly investment
    And the time series should end at the final portfolio value

  Scenario: Calculate DCA investment returns
    When I run the DCA simulation
    Then I should see the total amount invested
    And I should see the final portfolio value
    And I should see the total return on invested capital
    And I should see the annualized return on invested capital

  Scenario: Compare DCA to lump-sum and benchmark
    When I run the DCA simulation
    Then I should see the DCA final value
    And I should see what a lump-sum investment would have returned
    And I should see what the benchmark returned over the same period

  Scenario: Generate a full DCA report
    When I run the DCA simulation
    Then the DCA report should contain a summary section
    And the DCA report should contain an investment history section
    And the DCA report should contain a rebalancing log section
    And the DCA report should contain a comparison section
