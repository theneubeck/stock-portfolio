Feature: Portfolio list and detail pages
  As an investor
  I want to see all my portfolios in one list
  And click on any portfolio to see its full analysis
  So that I can compare everything on a single dimension

  Scenario: Homepage lists all portfolios
    When I request the homepage
    Then the response status should be 200
    And the page should contain "PORTFOLIOS"
    And the page should contain "Global Multi-Asset"
    And the page should contain "S&amp;P 500"
    And the page should contain "Nasdaq 100"
    And the page should contain "EURO STOXX 50"
    And the page should contain "Sweden"
    And the page should contain "Equal Weight"
    And the page should contain "Heavy Gold"
    And the page should contain "All Weather"
    And the page should contain "Total Return"

  Scenario: Portfolio detail page loads
    When I request the detail page for "global-multi-asset"
    Then the response status should be 200
    And the page should contain "Global Multi-Asset"
    And the page should contain "Allocation"
    And the page should contain "Performance"
    And the page should contain "Risk"
    And the page should contain "Statistics"

  Scenario: Benchmark detail page loads
    When I request the detail page for "sp500"
    Then the response status should be 200
    And the page should contain "S&amp;P 500"
    And the page should contain "Performance"
    And the page should contain "Risk"

  Scenario: Portfolio detail shows holding symbols
    When I request the detail page for "global-multi-asset"
    Then the page should contain "GLD"
    And the page should contain "ACWI"

  Scenario: API returns all portfolios
    When I request the portfolios API
    Then the response status should be 200
    And the response should be valid JSON
    And the JSON should be a list
    And the JSON list should have at least 5 items

  Scenario: API returns single portfolio detail
    When I request the portfolio API for "global-multi-asset"
    Then the response status should be 200
    And the response should be valid JSON
    And the JSON should contain key "summary"
    And the JSON should contain key "risk"

  Scenario: Unknown portfolio returns 404
    When I request the detail page for "nonexistent"
    Then the response status should be 404
