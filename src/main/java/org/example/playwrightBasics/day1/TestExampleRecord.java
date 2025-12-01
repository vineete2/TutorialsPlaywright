package org.example.playwrightBasics.day1;

import com.microsoft.playwright.*;
import com.microsoft.playwright.options.*;
import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;

public class TestExampleRecord {
    public static void main(String[] args) {
        try (Playwright playwright = Playwright.create()) {
            Browser browser = playwright.chromium().launch(new BrowserType.LaunchOptions()
                    .setHeadless(false));
            BrowserContext context = browser.newContext();
            Page page = context.newPage();
            page.navigate("https://demo.playwright.dev/todomvc/#/");
            page.getByRole(AriaRole.TEXTBOX, new Page.GetByRoleOptions().setName("What needs to be done?")).click();
            page.getByRole(AriaRole.TEXTBOX, new Page.GetByRoleOptions().setName("What needs to be done?")).fill("test cases");
            page.getByText("Double-click to edit a todo").click();
            page.getByText("Double-click to edit a todo").dblclick();
            page.getByRole(AriaRole.LINK, new Page.GetByRoleOptions().setName("Remo H. Jansen")).click();
            page.locator("span").filter(new Locator.FilterOptions().setHasText("Remo H. Jansen")).click();
        }
    }
}