package org.example.day34;

//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/blob/main/src/test/java/locators/

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

import java.util.List;

public class LocateByLinkTextAttribute {

    String url = "https://www.tutorialspoint.com/selenium/practice/links.php";
    String url2 = "https://www.tutorialspoint.com/selenium/practice/selenium_automation_practice.php";
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
    public void openUrl() throws InterruptedException{
        page.navigate(url);
        page.waitForLoadState();
    }

    @Test (priority = 0)
    public void locateByLinkText() throws InterruptedException {
        System.out.println("locateByLinkText " );
        ElementHandle element = page.querySelector("a:has-text(\"Home\")");
        element.click();
        Thread.sleep(5000);
    }


    @Test (priority = 1)
    public void locateByName() throws InterruptedException {
        page.navigate(url2);
        System.out.println("locateByName " );
        ElementHandle element = page.querySelector("[name='name']");
        element.fill("John Doe");
        Thread.sleep(3000);
    }

    @Test (priority = 2)
    public void locateByTagName() throws InterruptedException {
        List<ElementHandle> elements = page.querySelectorAll("a");
        System.out.println("locateByTagName " );
        int count = elements.size();
        System.out.println("Number of 'a' elements (links) found: " + count);

        // You can loop through the elements and perform actions
        for (ElementHandle element : elements) {
            String href = element.getAttribute("href");
            System.out.println("Link: " + href);
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