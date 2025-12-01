
@tag
Feature: Login Functionality

  @tag1
  Scenario: valid login
    Given user launches the application
    When user logs with valid username and password
    #When user logs with invalid username "Admin" and "admin123"
    Then user should see the dashboard


  Scenario: in-valid login
    Given user launches the application
    When user logs with invalid username "Admin" and "Admin"
    Then user should see an error message "Invalid credentials"