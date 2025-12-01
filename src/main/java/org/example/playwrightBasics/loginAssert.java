package org.example.playwrightBasics;

import com.microsoft.playwright.Browser;
import com.microsoft.playwright.BrowserType;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;
import org.testng.annotations.AfterTest;
import org.testng.annotations.BeforeTest;
import org.testng.annotations.Test;

import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;
import static org.testng.Assert.assertEquals;

public class loginAssert {
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
        page.navigate("https://app.vwo.com/#/login");


        page.locator("#login-username").fill( "tiveh19880@mogash.com");

        page.locator("#login-password").fill("TesterLogin@1457");
        page.click("#js-login-btn");
        page.waitForSelector(".page-heading");
        String heading = page.textContent( ".page-heading");
        String spanInnerText = page.textContent( "[data-qa=\"cogoyawado\"]");
        System.out.println(" Page Heading is "+heading);
        System.out.println(" Page Inner Text is "+spanInnerText);
        /// https://playwright.dev/java/docs/assertions
      //  assertEquals( "Dashboard", heading);  // AssertionError: as heading Expected :Set Up Your Account  Actual   :Dashboard
          assertEquals( "Set Up Your Account", heading,"works"); //works fine
    }
    @AfterTest
    public void teardown() {
        page.close();
    }

}
