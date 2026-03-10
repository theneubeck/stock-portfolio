Feature: Sortable table columns
  As an investor
  I want to click table column headers to sort rows
  So that I can quickly find the best or worst portfolios by any metric

  Scenario: Homepage tables have sortable column headers
    When I request the homepage
    Then the response status should be 200
    And the page should contain "sortable"
    And the page should contain "data-sort"

  Scenario: Detail page tables have sortable column headers
    When I request the detail page for "global-multi-asset"
    Then the response status should be 200
    And the page should contain "sortable"

  Scenario: Rolling page table has sortable column headers
    When I request the rolling returns page for "sp500" with horizon 5
    Then the response status should be 200
    And the page should contain "sortable"
