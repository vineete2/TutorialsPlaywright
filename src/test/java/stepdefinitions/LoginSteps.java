package stepdefinitions;

//src https://github.com/lokesh771988/PlaywrightJavaCucumberTestNG/blob/master/src/test/java/stepdefinitions/LoginSteps.java


import com.microsoft.playwright.*;
import io.cucumber.java.en.*;
import org.testng.Assert;
import pages.LoginPage;

//import java.io.IO;
import java.util.List;
import java.util.Map;

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
        browser =  playwright.chromium().launch(new BrowserType.LaunchOptions().setHeadless(true));
       // browser = playwright.firefox().launch(new BrowserType.LaunchOptions().setHeadless(true));
      //  browser = playwright.webkit().launch(new BrowserType.LaunchOptions().setHeadless(true));
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

    @When("user logs with valid username {string} and {string}")
    public void login_page(String username, String password) throws InterruptedException {
        login = new LoginPage(page);
        login.loginPage(username, password);
        System.out.println("Login Page credentials");
        Thread.sleep(5000);

    }
    @Then("user should see the dashboard")
    public void verify_dashboard() throws InterruptedException {
        Thread.sleep(5000);
        System.out.println("Dashboard");
        assertTrue(page.locator(".oxd-main-menu-item").first().isVisible());
        context.close();
        page.close();

    }


    @When("user logs with invalid username {string} and password {string}")
    public void user_logs_with_invalid_username_and_Password(String username, String password) throws InterruptedException {

        System.out.println("Attempting login with invalid credentials: " + username + "/" + password);
        login = new LoginPage(page);
        login.loginPage(username, password);
        System.out.println("Login Page");
        Thread.sleep(5000);

    }

    @Then("user should see an error message {string}")
    public void verify_login_error_message(String expectedMessage) throws InterruptedException {
        Thread.sleep(5000);
        //assertTrue(page.locator("//*[text()='Invalid credentials']").isVisible());
        login=new LoginPage(page);
        String lbl_message = login.getLoginErrorMessage();
        Assert.assertEquals(lbl_message, expectedMessage);
      //  assertTrue(page.getByText("Invalid credentials").isVisible());
        System.out.println("Verifying error message: " + expectedMessage);
        context.close();
        page.close();
    }

    @When("user logs in with {string} and {string}")
    public void user_login(String username, String password) throws InterruptedException {
        login = new LoginPage(page);
        login.loginPage(username, password);
        System.out.println("multiple Login ");
        Thread.sleep(5000);
    }
    @Then("user should verify Message {string}")
    public void verify_message(String message)
    {
        if (message.equalsIgnoreCase("Dashboard"))
        {
            assertTrue(page.locator(".oxd-main-menu-item").first().isVisible());
            context.close();
            page.close();
        }
        else {
            assertTrue(page.locator("//*[text()='Invalid credentials']").isVisible());
            context.close();
            page.close();
        }

    }

    @When("user logs with credentials")
    public void userLogsWithCredentials(io.cucumber.datatable.DataTable dataTable) throws InterruptedException {
        List<Map<String, String>> credentials = dataTable.asMaps(String.class, String.class);
        String username = credentials.get(0).get("username");
        String password = credentials.get(0).get("password");
        login = new LoginPage(page);
        login.loginPage(username, password);
        System.out.println("Login Page smoke");
        Thread.sleep(5000);
    }
}
