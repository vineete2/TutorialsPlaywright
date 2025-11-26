package org.example.day36;

//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/tree/main/src/test/java/webdrivergetcommands

import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.Test;
import com.microsoft.playwright.Browser;
import com.microsoft.playwright.BrowserContext;
import com.microsoft.playwright.BrowserType;
import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;

public class webdriverGetCommands {

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


    //RetrieveAttributeValueByGetAttributeMethod
    @Test(priority = 0)
    public void getAttributeMethod() throws InterruptedException {
        Locator locator = page.locator("//input[@id='email']");
        String attributeValue = locator.getAttribute("placeholder");
        System.out.println(attributeValue);
        Thread.sleep(6000);
    }

    @Test(priority = 0)
    public void fetchCurrentURL() throws InterruptedException {
        String currentURL = page.url();
        System.out.println(currentURL);
        Thread.sleep(1000);
    }

    @Test(priority = 0)
    public void fetchPageSource() throws InterruptedException {
        String pageSource = page.content();
        System.out.println(pageSource);
        Thread.sleep(1000);
    }
    @Test(priority = 0)
    public void getTextMethod() throws InterruptedException {
        Locator locator = page.locator("//form[@id='practiceForm']/h1");
        System.out.println(locator.textContent());
        Thread.sleep(2000);
    }

    @Test(priority = 0)
    public void fetchClassInfo() throws InterruptedException {
        Class<? extends Page> className = page.getClass();
        System.out.println("className: " + className);
        Thread.sleep(1000);
    }


    @Test(priority = 0)
    public void fetchTitle() throws InterruptedException {
        String title = page.title();
        System.out.println(title);
        Thread.sleep(1000);
    }



    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }

}