Feature: Benchmark indices page
  As an investor
  I want to see buy-and-hold performance for major market indices
  So that I can compare my portfolio against global benchmarks

  Scenario: Benchmarks page loads successfully
    When I request the benchmarks page
    Then the response status should be 200
    And the page should contain "BENCHMARK INDICES"

  Scenario: Benchmarks page shows major index names
    When I request the benchmarks page
    Then the page should contain "S&amp;P 500"
    And the page should contain "Nasdaq 100"
    And the page should contain "EURO STOXX 50"
    And the page should contain "Sweden"

  Scenario: Benchmarks page shows performance data
    When I request the benchmarks page
    Then the page should contain "Total Return"
    And the page should contain "Annualized"
    And the page should contain "Volatility"
    And the page should contain "Max Drawdown"

  Scenario: Benchmarks API returns JSON
    When I request the benchmarks API endpoint
    Then the response status should be 200
    And the response should be valid JSON
    And the JSON should contain key "benchmarks"
    And the JSON should contain key "period"
