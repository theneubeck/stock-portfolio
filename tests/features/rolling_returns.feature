Feature: Rolling N-year return analysis
  As an investor
  I want to see the distribution of all possible N-year buy-and-hold returns
  So that I can understand the range of outcomes for holding an asset over that period

  Scenario: Calculate rolling 5-year returns from a price series
    Given a monthly price series rising steadily over 10 years
    When I calculate rolling 5-year returns
    Then I should get a series of 5-year return values
    And the number of rolling returns should equal the number of prices minus the 5-year offset

  Scenario: Rolling return statistics include mean and Sharpe
    Given a monthly price series rising steadily over 10 years
    When I calculate rolling 5-year return statistics
    Then the statistics should include "mean_return_pct"
    And the statistics should include "median_return_pct"
    And the statistics should include "best_return_pct"
    And the statistics should include "worst_return_pct"
    And the statistics should include "sharpe_ratio"
    And the statistics should include "positive_pct"

  Scenario: Web page shows rolling returns tab
    When I request the rolling returns page for "sp500" with horizon 5
    Then the response status should be 200
    And the page should contain "Rolling 5-Year Returns"
    And the page should contain "Mean Return"
    And the page should contain "Median Return"
    And the page should contain "Worst"
    And the page should contain "Best"

  Scenario: Rolling returns API returns JSON data
    When I request the rolling returns API for "sp500" with horizon 5
    Then the response status should be 200
    And the response should be valid JSON
    And the JSON should contain key "statistics"
    And the JSON should contain key "histogram"
