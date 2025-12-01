package org.example.playwrightBasics.day37;

//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/tree/main/src/test/java/windowhandling

import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.Test;
import com.microsoft.playwright.Browser;
import com.microsoft.playwright.BrowserContext;
import com.microsoft.playwright.BrowserType;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;

import java.util.List;

public class windowHandling {
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

    @Test
    public void createNewWindow() throws InterruptedException {
        System.out.println(" createNewWindow ");
        page.navigate("https://www.testingtherapy.com/");
        Thread.sleep(3000);

        Page secondWindow= browser.newContext().newPage();
        secondWindow.bringToFront();
        secondWindow.navigate("https://www.google.com/");
        Thread.sleep(3000);
    }

    @Test
    public void countWindows() throws InterruptedException {
        System.out.println(" countWindows ");

        page.navigate("https://www.testingtherapy.com/");
        Thread.sleep(3000);

        Page secondTab = browser.newContext().newPage();
        secondTab.bringToFront();
        secondTab.navigate("https://www.google.com/");
        Thread.sleep(3000);

        List<BrowserContext> allContexts = browser.contexts();
        int totalWindows = 0;
        for (BrowserContext ctx : allContexts) {
            totalWindows += ctx.pages().size();
        }

        System.out.println("Total number of windows: " + totalWindows);
    }


    @Test
    public void switchToWindow() throws InterruptedException {
        System.out.println(" switchToWindow ");

        page.navigate("https://www.testingtherapy.com/");
        Thread.sleep(3000);

        Page secondTab = browser.newContext().newPage();
        secondTab.bringToFront();
        secondTab.navigate("https://www.google.com/");
        Thread.sleep(3000);
    }

    @Test
    public void switchingWindow() throws InterruptedException {
        System.out.println(" switchingWindow ");

        page.navigate("https://www.testingtherapy.com/");
        Thread.sleep(3000);

        Page secondWindow = browser.newContext().newPage();
        secondWindow.bringToFront();
        secondWindow.navigate("https://www.google.com/");
        Thread.sleep(3000);

        page.bringToFront();
        Thread.sleep(3000);

        secondWindow.bringToFront();
        Thread.sleep(3000);

    }



    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}