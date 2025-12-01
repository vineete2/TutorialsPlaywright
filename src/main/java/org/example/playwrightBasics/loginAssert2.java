package org.example.playwrightBasics;

import com.microsoft.playwright.*;
import org.testng.annotations.AfterTest;
import org.testng.annotations.BeforeTest;
import org.testng.annotations.Test;

import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;
import static org.testng.Assert.assertEquals;

public class loginAssert2 {
    Playwright playwright;
    Browser browser;
    Page page;

    @BeforeTest
    public void setup() {
        playwright = Playwright.create();
        browser = playwright.chromium().launch(
                new BrowserType.LaunchOptions().setHeadless(false).setSlowMo(100)
        );
        page = browser.newPage();

    }

    //mvn exec:java -e -D exec.mainClass=com.microsoft.playwright.CLI -D exec.args="codegen https://app.vwo.com/#/login"

    @Test
    public void Login_Record() {
        // Navigate to the VWO login page
        page.navigate("https://app.vwo.com/#/login");

        // Assert that the login page is loaded by checking the URL
        assertThat(page).hasURL("https://app.vwo.com/#/login");

        // Assert that the username input field is visible and enabled
        Locator usernameInput = page.locator("#login-username");
        assertThat(usernameInput).isVisible();
        assertThat(usernameInput).isEnabled();

        // Assert that the username input has the correct placeholder attribute
      //  assertThat(usernameInput).hasAttribute("placeholder", "Enter your email address");

        // Fill in the username
        usernameInput.fill("tiveh19880@mogash.com");

        // Assert that the password input field is visible and editable
        Locator passwordInput = page.locator("#login-password");
        assertThat(passwordInput).isVisible();
        assertThat(passwordInput).isEditable();

        // Assert that the password input has a specific CSS property (e.g., type="password")
       // assertThat(passwordInput).hasAttribute("type", "password");

        // Fill in the password
        passwordInput.fill("TesterLogin@1457");

        // Assert that the login button is visible and has the correct text
        Locator loginButton = page.locator("#js-login-btn");
        assertThat(loginButton).isVisible();
        assertThat(loginButton).hasText("Sign in");

        // Assert that the login button has a specific CSS class
       // assertThat(loginButton).hasClass("btn--positive");

        // Click the login button
        loginButton.click();

        // Wait for the dashboard heading and assert it is visible
        Locator heading = page.locator(".page-heading");
        page.waitForSelector(".page-heading");
        assertThat(heading).isVisible();

        // Assert that the heading contains the expected text
        assertThat(heading).hasText("Set Up Your Account");

        // Assert that the heading is in the viewport
        assertThat(heading).isInViewport();

        // Retrieve and assert the span text content using data-qa attribute
        Locator span = page.locator("[data-qa='cogoyawado']");
        assertThat(span).isVisible();
      //  assertThat(span).containsText("Welcome"); // Assuming it contains "Welcome" or similar

        // Traditional TestNG assertion for comparison
        String headingText = heading.textContent();
        assertEquals(headingText, "Set Up Your Account", "Page heading matches expected value");

        // Assert that the page has the correct title after login
       // assertThat(page).hasTitle("VWO | #1 A/B Testing Tool in the World"); // Adjust based on actual title
    }
    @AfterTest
    public void teardown() {
        page.close();
    }

}
