package org.example.day32;

//src  https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/tree/main/src/test/java/formwebelementcommands

import com.microsoft.playwright.*;
import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.Test;

public class  formWebelementCommands{
    protected static String url = "https://www.tutorialspoint.com/selenium/practice/selenium_automation_practice.php";
    protected static String url2 = "https://www.facebook.com/";
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
        // Maximize the window by setting the viewport size to a large resolution
        page.setViewportSize(1920, 1080);
        System.out.println("**** Chrome Browser Version is : " + browser.version());
    }

    @BeforeClass
    public void openUrl() throws InterruptedException {
        page.navigate(url);
        page.waitForLoadState();
    }


    //ClearMethod
    @Test(priority = 0) // Executes 1st
    public void clearMethod() throws InterruptedException {
        Locator element = page.locator("//input[@id='name']");
        element.fill("James bond");
        Thread.sleep(3000);
        element.clear();
        Thread.sleep(3000);
    }

    @Test(priority = 0) // Executes 2nd
    public void clickMethod() throws InterruptedException {
        ElementHandle element = page.querySelector("#dob");
        element.click();
        Thread.sleep(5000);
    }


    @Test //executes 3rd
    public void sendKeysMethod() throws InterruptedException {
        Locator element = page.locator("//input[@id='name']");
        element.fill("James Pond");
        Thread.sleep(3000);
    }

    @Test (priority = 2) // Executes 4th
    public void submitMethod() throws InterruptedException {
        page.navigate(url2);
        page.waitForLoadState();
        ElementHandle email = page.querySelector("#email");
        ElementHandle pass = page.querySelector("#pass");

        email.fill("abc@gmail.com");
        Thread.sleep(3000);
        pass.fill("123456");
        Thread.sleep(3000);
        ElementHandle submitButton = page.querySelector("//button[@name='login']");
        submitButton.click();

        Thread.sleep(5000);
    }
    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}