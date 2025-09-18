package org.example.day2;

import com.microsoft.playwright.*;
import com.microsoft.playwright.options.WaitForSelectorState;
import org.testng.annotations.AfterTest;
import org.testng.annotations.BeforeTest;
import org.testng.annotations.Test;

import java.nio.file.Paths;

import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;

public class validatePage {


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
        public void Validate_Page() {
            page.navigate("https://app.vwo.com/#/login");

            // Wait until the input is visible in the DOM
            page.waitForSelector("input[name='username']",  /// by Name element
                    new Page.WaitForSelectorOptions().setState(WaitForSelectorState.VISIBLE));
            page.locator("#login-username").fill("tiveh19880@mogash.com");  //# is for By id

            //page.getByRole(AriaRole.TEXTBOX, new Page.GetByRoleOptions().setName("Email address")).fill("tiveh19880@mogash.com");
            // Wait for the password field
            Locator passwordField = page.locator("#login-password");
            passwordField.waitFor(new Locator.WaitForOptions()
                    .setState(WaitForSelectorState.VISIBLE));

            // Fill password
            passwordField.fill("TesterLogin@1457");

            // Wait for sign in button
            Locator signInButton = page.locator("#js-login-btn");
            signInButton.waitFor(new Locator.WaitForOptions()
                    .setState(WaitForSelectorState.ATTACHED));

            // Click the button
            signInButton.click();

            // "Get Started" link relative XPath
            Locator getStarted = page.locator("//a[@aria-label='Get started with VWO']");
            getStarted.waitFor(new Locator.WaitForOptions().setState(WaitForSelectorState.VISIBLE));
           // getStarted.click();

            if (getStarted.isVisible()) getStarted.click();

            // Wait until "Dashboard" link is ready and click
            String dashXPath = "//a[@aria-label='View dashboard']";
            page.waitForFunction(
                    "xpath => { const el = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue; return el && !el.classList.contains('disabled'); }",
                    dashXPath
            );
            page.locator("xpath=" + dashXPath).click();


            // Screenshots
            page.screenshot(new Page.ScreenshotOptions().setFullPage(true).setPath(Paths.get("screenshots/dashboard-full.png")));
          //  dashboardHeading.screenshot(new Locator.ScreenshotOptions().setPath(Paths.get("screenshots/dashboard-heading.png")));

        }
        @AfterTest
        public void teardown() {
            page.close();
        }

}


