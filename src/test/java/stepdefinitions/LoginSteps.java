package stepdefinitions;

//src https://github.com/lokesh771988/PlaywrightJavaCucumberTestNG/blob/master/src/test/java/stepdefinitions/LoginSteps.java


import com.microsoft.playwright.*;
import io.cucumber.java.en.*;
import pages.LoginPage;

import static org.testng.Assert.assertTrue;

public class LoginSteps {

    private static Playwright playwright;
    private static Browser browser;
    private static BrowserContext context;
    private static Page page;
    LoginPage login;

    @Given("user launches the application")
    public void launch_app() {
        System.out.println("Application launched");
        playwright = Playwright.create();
        browser =  playwright.chromium().launch(new BrowserType.LaunchOptions().setHeadless(false));
        context = browser.newContext();
        page = context.newPage();
        page.navigate("https://opensource-demo.orangehrmlive.com/web/index.php/auth/login");
    }

    @When("user logs with valid username and password")
    public void login_page() throws InterruptedException {
        login = new LoginPage(page);
        login.loginPage("Admin", "admin123");
        System.out.println("Login Page");
        Thread.sleep(5000);
    }

    @Then("user should see the dashboard")
    public void verify_dashboard() {
        System.out.println("Dashboard");
        assertTrue(page.locator(".oxd-main-menu-item").first().isVisible());

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
