
package iframehandling;

import com.microsoft.playwright.*;
import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.Test;

//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/tree/main/src/test/java/webtablehandling


public class SwitchToFramesByID {
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
    public void identifyIFramesById() throws InterruptedException {
        Thread.sleep(3000);
        System.out.println("identify by iframes ID: ");
        page.frame("frame1");
        ElementHandle text = page.querySelector("//*[text()='Selenium - Automation Practice Form']");
        System.out.println("TEXT MESSAGE: "+text.textContent());
    }

    @Test
    public void identifyIFramesByIndex() throws InterruptedException {
        Thread.sleep(3000);
        System.out.println("identify by iframes Index: ");
        Frame iframe = page.frames().get(0);
        ElementHandle text = iframe.querySelector("//*[text()='Selenium - Automation Practice Form']");
        System.out.println(text.textContent());
    }

    @Test
    public void identifyIFramesByName() throws InterruptedException {
        Thread.sleep(3000);
        System.out.println("identify by iframes Name: ");
        page.waitForSelector("iframe");
        Frame iframe = page.frame("frame1");
        ElementHandle text = iframe.querySelector("//*[text()='Selenium - Automation Practice Form']");
        System.out.println(text.textContent());
    }

    @Test
    public void identifyIFramesByWebElement() throws InterruptedException {
        Thread.sleep(3000);
        System.out.println("identify by iframes WebElement: ");
        ElementHandle iframeElement = page.querySelector("#frame1");
        Frame frame = iframeElement.contentFrame();
        page = frame.page();

        ElementHandle textElement = page.waitForSelector("//*[text()='Selenium - Automation Practice Form']");
        String text = textElement.textContent();

        System.out.println("Text inside the iframe: " + text);
    }



    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}