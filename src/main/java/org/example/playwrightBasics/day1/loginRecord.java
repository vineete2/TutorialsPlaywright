package org.example.playwrightBasics.day1;

import com.microsoft.playwright.Browser;
import com.microsoft.playwright.BrowserType;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;
import com.microsoft.playwright.options.AriaRole;
import org.testng.annotations.AfterTest;
import org.testng.annotations.BeforeTest;
import org.testng.annotations.Test;

import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;

public class loginRecord {
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
        page.getByRole(AriaRole.TEXTBOX, new Page.GetByRoleOptions().setName("Email address")).click();
        page.getByRole(AriaRole.TEXTBOX, new Page.GetByRoleOptions().setName("Email address")).fill("tiveh19880@mogash.com");
        page.getByRole(AriaRole.TEXTBOX, new Page.GetByRoleOptions().setName("Password")).click();
        page.getByRole(AriaRole.TEXTBOX, new Page.GetByRoleOptions().setName("Password")).fill("TesterLogin@1457");
        page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("Sign in").setExact(true)).click();
        page.getByRole(AriaRole.LINK, new Page.GetByRoleOptions().setName("Go to Dashboard").setExact(true)).click();
        page.getByLabel("View dashboard").click();
        page.getByRole(AriaRole.HEADING, new Page.GetByRoleOptions().setName("Dashboard")).click();
        assertThat(page.getByRole(AriaRole.HEADING, new Page.GetByRoleOptions().setName("Dashboard"))).isVisible();

    }
    @AfterTest
    public void teardown() {
        page.close();
    }

}
