package org.example.day34;

//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/blob/main/src/test/java/locators/

import com.microsoft.playwright.*;
import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.Test;

public class locateBy {

    String url = "https://www.tutorialspoint.com/selenium/practice/register.php";

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
        //context = browser.newContext(new Browser.NewContextOptions());

        context = browser.newContext();
        page = context.newPage();
        page.setViewportSize(1920, 1080);
        System.out.println("**** Chrome Browser Version is : " + browser.version());
    }

    @BeforeClass
    public void openUrl() throws InterruptedException{
        page.navigate(url);
        page.waitForLoadState();
    }

    @Test // locate by class
    public void locateByClassName() throws InterruptedException {
        Locator formControls = page.locator(".form-control");
        page.waitForSelector(".form-control");
        int count = formControls.count();
        Thread.sleep(3000);
        System.out.println("Found " + count + " elements with class 'form-control'");
        if (count > 0) {
            formControls.first().click();
            formControls.first().fill("John Doe");
            Thread.sleep(3000);
        }
    }

    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }

}