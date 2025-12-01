package stepdefinitions;

//src https://github.com/lokesh771988/PlaywrightJavaCucumberTestNG/blob/master/src/test/java/stepdefinitions/LoginSteps.java


import io.cucumber.java.en.*;

public class LoginSteps {

    @Given("user launches the application")
    public void launch_app() {
        System.out.println("Application launched");
    }

    @When("user logs with valid username and password")
    public void login_page() {
        System.out.println("Login Page");
    }

    @Then("user should see the dashboard")
    public void verify_dashboard() {
        System.out.println("Dashboard");

    }


    @When("user logs with invalid username {string} and {string}")
    public void user_logs_with_invalid_username_and(String username, String password) {

        System.out.println("Attempting login with invalid credentials: " + username + "/" + password);
    }

    @Then("user should see an error message {string}")
    public void user_should_see_an_error_message(String expectedMessage) {

        System.out.println("Verifying error message: " + expectedMessage);
    }
}
