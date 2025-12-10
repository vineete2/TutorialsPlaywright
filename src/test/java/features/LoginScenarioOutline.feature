@Regression
Feature: login With Scenario Outlines

  Background:
    Given user launches the application

  @tag2
  Scenario Outline: login with Multiple Credentials
    When user logs in with "<userName>" and "<password>"
    Then user should verify Message "<message>"

    Examples:
      | userName | password | message             |
      | Admin    | admin123 | Dashboard           |
      | Admin    | Admin    | Invalid credentials |

  @smoke
  Scenario: login with Data Table
    When user logs with credentials
      | username | password |
      | Admin    | admin123 |
    Then user should see the dashboard