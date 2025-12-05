package pages;

import com.microsoft.playwright.Page;

public class LoginPage {

    private Page page;


    // session object
    //When creating a page object, passing in the Playwright page/session ensures all locators and actions
    // use the same browser context—avoiding errors like "element not found" or referencing a closed driver.

    //the class will hold locators and methods for login actions
    public LoginPage(Page page) {
        this.page = page;
    }

    private String txtName = "[name='username']";
    private String txtPassword = "[name='password']";
    private String btnLogin = "//button[text()=' Login ']";
    private String login_error_message = "//*[text()='Invalid credentials']";

    public void loginPage(String name, String password) {
        page.fill(txtName, name);
        page.fill(txtPassword, password);
        page.click(btnLogin);
    }

    public String getLoginErrorMessage() {
        return page.locator(login_error_message).textContent();
    }
}