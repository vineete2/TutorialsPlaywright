package org.example.day35;

//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/blob/main/src/test/java/locators/dynamicxpath/LocateByStartsWith.java

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

public class LocateByStartsWith {
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

    @Test(priority = 0)
    public void locateByStartsWith() throws InterruptedException {
        ElementHandle xpathByStartWith = page.querySelector("//*[starts-with(@id,'name')]");
        xpathByStartWith.fill("John");
        Thread.sleep(3000);
    }

    @Test(priority = 0)
    public void locateByText() throws InterruptedException {
        ElementHandle xpathByTextFunction = page.querySelector("//*[text()='Student Registration Form']");
        System.out.println(xpathByTextFunction.textContent());
        Thread.sleep(3000);
    }
    @Test(priority = 0)
    public void locateByPreceding() throws InterruptedException {
        ElementHandle xpathByPreceding = page.querySelector("//input[@id='email']//preceding::input[1]");
        xpathByPreceding.fill("Doe");
        Thread.sleep(3000);
    }

    @Test(priority = 0)
    public void locateByOr() throws InterruptedException {
        // Syntax: //*[first condition and second condition and ....]
        ElementHandle xpathByOr = page.querySelector("//*[contains(@id,'name') or @placeholder='First Name'] ");
        xpathByOr.fill("Kates");
        Thread.sleep(3000);
    }

    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}