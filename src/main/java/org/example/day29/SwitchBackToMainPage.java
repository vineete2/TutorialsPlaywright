package org.example.day29;


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

//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/tree/main/src/test/java/webtablehandling


public class SwitchBackToMainPage {
    protected static String url = "https://www.tutorialspoint.com/selenium/practice/nestedframes.php";

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


    @Test
    public void backToMain() throws InterruptedException {
        page.frame("frame1");
        ElementHandle text = page.querySelector("//*[text()='Selenium - Automation Practice Form']");
        System.out.println(text.textContent());
        Thread.sleep(3000);
        // Switch back to the main window
        page.mainFrame();

        ElementHandle textInMainPage = page.querySelector("//*[text()='Nested Frames']");
        System.out.println(textInMainPage.textContent());
        Thread.sleep(3000);
    }

    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}
