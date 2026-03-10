Feature: Portfolio detail web page
  As an investor
  I want to view detailed analysis for any portfolio
  So that I can understand its allocation, performance, and risk

  Scenario: Detail page loads for multi-holding portfolio
    When I request the detail page for "global-multi-asset"
    Then the response status should be 200
    And the page should contain "Global Multi-Asset"

  Scenario: Detail page shows allocation breakdown
    When I request the detail page for "global-multi-asset"
    Then the page should contain "Allocation"
    And the page should list each holding symbol

  Scenario: Detail page shows performance metrics
    When I request the detail page for "global-multi-asset"
    Then the page should contain "Performance"
    And the page should contain "Total Return"
    And the page should contain "Annualized"

  Scenario: Detail page shows risk metrics
    When I request the detail page for "global-multi-asset"
    Then the page should contain "Risk"
    And the page should contain "Volatility"
    And the page should contain "Sharpe"
    And the page should contain "Drawdown"

  Scenario: Detail page shows statistics section
    When I request the detail page for "global-multi-asset"
    Then the page should contain "Statistics"
    And the page should contain "Peak"
    And the page should contain "Trough"

  Scenario: Single-holding portfolio loads
    When I request the detail page for "sp500"
    Then the response status should be 200
    And the page should contain "Performance"
    And the page should contain "Risk"

  Scenario: API returns portfolio detail JSON
    When I request the portfolio API for "global-multi-asset"
    Then the response status should be 200
    And the response should be valid JSON
    And the JSON should contain key "summary"
    And the JSON should contain key "allocation"
    And the JSON should contain key "risk"

  Scenario: API returns all portfolios list
    When I request the portfolios API
    Then the response status should be 200
    And the response should be valid JSON
