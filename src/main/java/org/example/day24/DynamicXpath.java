package org.example.day24;
//Source: https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java

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

public class DynamicXpath {
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
    public void openUrl() throws InterruptedException{
        page.navigate(url);
        page.waitForLoadState();
    }

    @Test(priority = 0)
    public void locateByAND() throws InterruptedException {
        //Syntax: //*[first condition and second condition and ....]
        ElementHandle xpathByAND = page
                .querySelector("//*[contains(@id,'name') and @placeholder='First Name'] ");
        xpathByAND.fill("Tom Hanks");
        Thread.sleep(3000);
    }

    @Test(priority = 1)
    public void locateByContiansExample02() throws InterruptedException {
        // Syntax: //*[contains(@attribute, 'value')]
        ElementHandle byAttribute = page.querySelector("//*[contains(@id,'name')]");
        byAttribute.fill("Brad Pitt");
        Thread.sleep(3000);
    }

    @Test(priority = 2)
    public void clickMethod() throws InterruptedException {

        page.navigate("https://www.tutorialspoint.com/selenium/practice/webtables.php");
        ElementHandle xpathByLast = page.querySelector("//table[@class='table table-striped mt-3']/tbody/tr[last()]/td[4]");
        System.out.println(xpathByLast.textContent());
        Thread.sleep(3000);
    }

    @Test(priority = 0)
    public void locateByOr() throws InterruptedException {
        // Syntax: //*[first condition and second condition and ....]
        ElementHandle xpathByOr = page.querySelector("//*[contains(@id,'name') or @placeholder='First Name'] ");
        xpathByOr.fill("Robert");
        Thread.sleep(3000);
    }


    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}