package org.example.playwrightBasics.day1;

import com.microsoft.playwright.Browser;
import com.microsoft.playwright.BrowserType;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;
import com.microsoft.playwright.options.AriaRole;
import org.testng.annotations.AfterTest;
import org.testng.annotations.BeforeTest;
import org.testng.annotations.Test;

import java.nio.file.Paths;

import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;
import static org.testng.AssertJUnit.assertEquals;

public class SelectorsRecord {

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

    // mvn exec:java -e -D exec.mainClass=com.microsoft.playwright.CLI -D exec.args="codegen selectorshub.com/xpath-practice-page"
    @Test
    public void Selectors_Record() {
        page.navigate("https://selectorshub.com/xpath-practice-page/");
        page.getByRole(AriaRole.TEXTBOX, new Page.GetByRoleOptions().setName("Email")).click();
        page.getByRole(AriaRole.TEXTBOX, new Page.GetByRoleOptions().setName("Email")).fill("tester@email.com");
        page.getByRole(AriaRole.TEXTBOX, new Page.GetByRoleOptions().setName("Password")).fill("Test1234");
        page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("Submit")).click();

       //Below line fails as there is no element as such on website
        assertThat(page.getByRole(AriaRole.HEADING, new Page.GetByRoleOptions().setName("Dashboard"))).isVisible();



    }

    @AfterTest
    public void teardown() {
        page.close();
    }

}
