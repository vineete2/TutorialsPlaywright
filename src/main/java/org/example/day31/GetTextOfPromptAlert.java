package org.example.day31;


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

//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/tree/main/src/test/java/alerthandling


public class GetTextOfPromptAlert {
    protected static String url = "https://www.tutorialspoint.com/selenium/practice/alerts.php";

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

    @Test(priority = 0)
    public void getTextOfAlert() throws InterruptedException {
        page.onDialog(dialog -> {
            System.out.println("Dialog Type: " + dialog.type());
            System.out.println("Dialog Message: " + dialog.message());
            dialog.accept();

        });
        ElementHandle element = page.querySelector("//button[@onclick='myPromp()']");
        element.click();
        Thread.sleep(7000);
    }

    @Test(priority = 1)
    public void sendText() throws InterruptedException {

        page.onDialog(dialog -> {
            System.out.println("Dialog Type: " + dialog.type());
            System.out.println("Dialog Message: " + dialog.message());

            if (dialog.type().equals("alert")) {
                dialog.accept();
                System.out.println("Accepted Alert.");
            } else if (dialog.type().equals("confirm")) {
                dialog.accept();
                System.out.println("Accepted Confirmation.");
            } else if (dialog.type().equals("prompt")) {
                dialog.accept("Hello - Playwright");
                System.out.println("Accepted Prompt with Text.");
            }
        });
        ElementHandle element = page.querySelector("//button[@onclick='myPromp()']");
        element.click();
        Thread.sleep(10000);
    }


    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}
