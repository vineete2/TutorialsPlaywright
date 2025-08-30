package org.example;

import com.microsoft.playwright.Browser;
import com.microsoft.playwright.BrowserType;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;
import com.microsoft.playwright.options.LoadState;
import org.testng.annotations.Test;

import java.nio.file.Paths;

import static org.testng.AssertJUnit.assertEquals;

public class Login {


    @Test
    public void Verify_login() {
        Playwright playwright = Playwright.create();
            Browser browser = playwright.chromium().launch(
                    new BrowserType.LaunchOptions().setHeadless(false).setSlowMo(100)
            );
            Page page = browser.newPage();
            page.navigate("https://app.vwo.com/#/login");
            System.out.println(page.title());
            page.locator("#login-username").fill("93npu2yyb@@esiix.com");
            page.locator("#login-password").fill("Wingify@123");
            page.click("#js-login-btn");
            page.waitForLoadState(LoadState.NETWORKIDLE);
            assertEquals("Dashboard",page.title());
            page.screenshot(new Page.ScreenshotOptions().setPath(Paths.get("Dashboard.png")));
            page.close();

    }

}
