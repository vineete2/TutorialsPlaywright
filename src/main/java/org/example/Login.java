package org.example;

import com.microsoft.playwright.Browser;
import com.microsoft.playwright.BrowserType;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;
import com.microsoft.playwright.options.LoadState;
import org.testng.annotations.AfterTest;
import org.testng.annotations.BeforeTest;
import org.testng.annotations.Test;

import java.nio.file.Paths;

import static org.testng.AssertJUnit.assertEquals;

public class Login {
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

    @Test
    public void Verify_login() {

            page.navigate("https://app.vwo.com/#/login");
            System.out.println(page.title());

            //# is used for IDs && (DOT ".") is used for class ids
            page.locator("#login-username").fill("tiveh19880@mogash.com");
            page.locator("#login-password").fill("TesterLogin@1457");
            page.click("#js-login-btn");
            page.waitForSelector(".page-heading"); //wait for a class to load
           // page.waitForLoadState(LoadState.NETWORKIDLE);
            assertEquals("Dashboard",page.title());
            page.screenshot(new Page.ScreenshotOptions().setPath(Paths.get("Dashboard.png")));


    }

    @AfterTest
    public void teardown() {
        page.close();
    }
}
