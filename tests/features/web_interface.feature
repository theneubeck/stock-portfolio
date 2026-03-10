Feature: Lightweight web dashboard
  As an investor
  I want a read-only web interface to view my portfolio analysis
  So that I can quickly check performance in a browser

  Scenario: Dashboard page loads successfully
    When I request the dashboard page
    Then the response status should be 200
    And the page should contain "PORTFOLIO ANALYSIS"

  Scenario: Dashboard shows allocation breakdown
    When I request the dashboard page
    Then the page should contain "Allocation"
    And the page should list each holding symbol

  Scenario: Dashboard shows performance metrics
    When I request the dashboard page
    Then the page should contain "Performance"
    And the page should contain "Total Return"
    And the page should contain "Annualized"

  Scenario: Dashboard shows risk metrics
    When I request the dashboard page
    Then the page should contain "Risk"
    And the page should contain "Volatility"
    And the page should contain "Sharpe"
    And the page should contain "Drawdown"

  Scenario: Dashboard shows statistics section
    When I request the dashboard page
    Then the page should contain "Statistics"
    And the page should contain "Peak"
    And the page should contain "Trough"

  Scenario: Comparison page loads successfully
    When I request the comparison page
    Then the response status should be 200
    And the page should contain "STRATEGY COMPARISON"

  Scenario: Comparison page shows strategy ranking
    When I request the comparison page
    Then the page should contain "Equal Weight"
    And the page should contain "Heavy Gold"
    And the page should contain "Total Return"

  Scenario: API returns portfolio JSON
    When I request the portfolio API endpoint
    Then the response status should be 200
    And the response should be valid JSON
    And the JSON should contain key "summary"
    And the JSON should contain key "allocation"
    And the JSON should contain key "risk"

  Scenario: API returns comparison JSON
    When I request the comparison API endpoint
    Then the response status should be 200
    And the response should be valid JSON
    And the JSON should contain key "strategies"
    And the JSON should contain key "ranking"
