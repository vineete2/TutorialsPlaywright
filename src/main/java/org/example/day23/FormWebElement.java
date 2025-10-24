package org.example.day23;


import com.microsoft.playwright.*;
import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.Test;

public class FormWebElement {
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
    public void clickMethod() throws InterruptedException {
        ElementHandle element = page.querySelector("#dob");
        element.click();
        Thread.sleep(5000);
    }

    @Test(priority = 1)
    public void clearMethod() throws InterruptedException {
        Locator element = page.locator("//input[@id='name']");
        element.fill("Ebrahim Hossain");
        Thread.sleep(3000);
        element.clear();
        Thread.sleep(3000);
    }
    @Test(priority = 2)
    public void sendKeysMethod() throws InterruptedException {
        Locator element = page.locator("//input[@id='name']");
        element.fill("Ebrahim Hossain");
        Thread.sleep(3000);
    }

    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}