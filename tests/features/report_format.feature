Feature: Report formatting
  As an investor
  I want a readable text report of my portfolio analysis
  So that I can quickly understand my portfolio's status

  Scenario: Format a report from analysis results
    Given a completed analysis report
    When I format the report as text
    Then the text should contain "PORTFOLIO ANALYSIS REPORT"
    And the text should contain "ALLOCATION"
    And the text should contain "PERFORMANCE"
    And the text should contain "RISK METRICS"
    And the text should contain "BENCHMARK COMPARISON"
