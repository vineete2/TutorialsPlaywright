package org.example.day31;

import com.microsoft.playwright.*;
import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.Test;

import static java.lang.Thread.sleep;
//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/tree/main/src/test/java/alerthandling

public class alertHandling {
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

    @Test(priority = 6)
    public void acceptAlert() throws InterruptedException {

        page.onDialog(dialog -> {
            System.out.println("Dialog Type: " + dialog.type());
            System.out.println("Dialog Message: " + dialog.message());
            try {
                sleep(3000);
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
            dialog.accept();
            System.out.println("Accepted Alert.");

        });

        Locator alertButton = page.locator("//button[@onclick='showAlert()']");
        alertButton.click();
        sleep(2000);

    }

    // Reusable dialog handler
    private void handleDialog(Dialog dialog, String promptText) throws InterruptedException {
        System.out.println("Dialog Type: " + dialog.type());
        System.out.println("Dialog Message: " + dialog.message());

        switch (dialog.type()) {
            case "alert":
                sleep(3000);
                dialog.accept();
                System.out.println("Accepted Alert.");
                break;

            case "confirm":
                sleep(3000);
                dialog.accept();
                System.out.println("Accepted Confirmation.");
                break;

            case "prompt":
                sleep(3000);
                dialog.accept(promptText);
                System.out.println("Accepted Prompt with Text: " + promptText);
                break;

            default:
                dialog.dismiss();
                System.out.println("Dialog dismissed.");
        }
    }

    @Test(priority = 0)
    public void acceptAlertOptimized() throws InterruptedException {

        page.onDialog(dialog -> {
            try {
                handleDialog(dialog, "Prompt Input");
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        });

        page.locator("//button[@onclick='myPromp()']").click();
        sleep(3000);
    }

    @Test(priority = 1)
    public void acceptConfirmAlertOptimized() throws InterruptedException {

        page.onDialog(dialog -> {
            try {
                handleDialog(dialog, "Entered text for prompt");
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        });

        page.locator("//button[@onclick='myDesk()']").click();
        sleep(3000);
    }

    @Test(priority = 2)
    public void dismissAlert() throws InterruptedException {

        page.onDialog(dialog -> {
            try {
                handleDialog(dialog, "Entered text for prompt");
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        });
        Locator alertButton = page.locator("//button[@id='confirmButton']");
        alertButton.click();
        sleep(3000);
    }


    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}
