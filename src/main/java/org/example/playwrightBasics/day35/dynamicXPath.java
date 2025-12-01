package org.example.playwrightBasics.day35;

//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/tree/main/src/test/java/locators/dynamicxpath

import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.Test;
import com.microsoft.playwright.Browser;
import com.microsoft.playwright.BrowserContext;
import com.microsoft.playwright.BrowserType;
import com.microsoft.playwright.ElementHandle;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;

public class dynamicXPath {
    protected static String url = "https://www.tutorialspoint.com/selenium/practice/selenium_automation_practice.php";

    Playwright playwright;
    BrowserType browserType;
    protected Browser browser;
    protected BrowserContext context;
    protected Page page;

    @BeforeSuite
    public void startChromeBrowser() {
        playwright = Playwright.create();
        browserType = playwright.chromium();
        browser = browserType.launch(new BrowserType.LaunchOptions().setHeadless(false));
        context = browser.newContext(new Browser.NewContextOptions());

        page = browser.newPage();
        System.out.println("**** Chrome Browser Version is : " + browser.version());
    }

    @BeforeClass
    public void openUrl() throws InterruptedException {
        page.navigate(url);
        page.waitForLoadState();
    }

    @Test(priority = 1)
    public void locateByContiansExample02() throws InterruptedException {
        // Syntax: //*[contains(@attribute, 'value')]
        ElementHandle byAttribue = page.querySelector("//*[contains(@id,'name')]");
        byAttribue.fill("john");
        Thread.sleep(3000);
    }

    @Test(priority = 0)
    public void locateByAND() throws InterruptedException {
        //Syntax: //*[first condition and second condition and ....]
        ElementHandle xpathByAND = page
                .querySelector("//*[contains(@id,'name') and @placeholder='First Name'] ");
        xpathByAND.fill("Thomas");
        Thread.sleep(3000);
    }

    @Test(priority = 0)
    public void locateByOr() throws InterruptedException {
        // Syntax: //*[first condition and second condition and ....]
        ElementHandle xpathByOr = page.querySelector("//*[contains(@id,'name') or @placeholder='First Name'] ");
        xpathByOr.fill("Doe");
        Thread.sleep(3000);
    }

    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}