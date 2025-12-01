package org.example.playwrightBasics.day30;

import com.microsoft.playwright.*;
import org.testng.Assert;
import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.Test;
import org.testng.asserts.SoftAssert;

//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/tree/main/src/test/java/assertions

public class Assertions {
    String url = "https://www.tutorialspoint.com/selenium/practice/selenium_automation_practice.php";

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
        // Create a new context with the options for maximized window size
      //  context = browser.newContext(new Browser.NewContextOptions().setViewportSize(1920, 1080));
        context = browser.newContext();
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

    @Test
    public void testAssertEquals() throws InterruptedException {

        Thread.sleep(3000);
        String actualTitle = page.title();
        String expectedTitle = "Selenium Practice - Student Registration Form";

        try {
            Assert.assertEquals(actualTitle, expectedTitle);
            System.out.println("Test Passed: The actual title is equal to the expected title.");
        } catch (AssertionError e) {
            System.out.println("Test Failed: The actual title is NOT equal to the expected title.");
            System.out.println("Actual Title: " + actualTitle);
            System.out.println("Expected Title: " + expectedTitle);
        }
    }

    @Test
    public void testAssertFalse() throws InterruptedException {
        Thread.sleep(3000);
        boolean verifyTitle = page.title().equalsIgnoreCase("Selenium Practice - Student Registration");
       // System.out.println(verifyTitle);
        Assert.assertFalse(verifyTitle);
        System.out.println("Test assertFalse Title: "+verifyTitle);
    }

    @Test
    public void testAssertTrue() throws InterruptedException {
        Thread.sleep(3000);
        ElementHandle element = page.querySelector("#hobbies");
        element.click();
        System.out.println("Test assertTrue element: "+element.isChecked());
        Assert.assertTrue(element.isChecked());

    }

    @Test
    public void testAssertNotEquals() throws InterruptedException {
        Thread.sleep(3000);
        String actualText = page.querySelector("body").textContent();
        String expectedText = "Not the expected text";
        try {
            Assert.assertNotEquals(actualText, expectedText);
            System.out.println("Test Passed: The actual text is NOT equal to the expected text.");
        } catch (AssertionError e) {
            System.out.println("Test Failed: The actual text is equal to the expected text.");
            System.out.println("Actual Text: " + actualText);
            System.out.println("Expected Text: " + expectedText);
        }
    }
    @Test
    public void testAssertNotNull() throws InterruptedException {
        Thread.sleep(3000);
        String actualTitle = page.title();

        // Check if the title is not null
        try {
            Assert.assertNotNull("Title should not be null", actualTitle);
            System.out.println("Test Passed: Page title is not null.");
        } catch (AssertionError e) {
            System.out.println("Test Failed: Page title is null.");
        }
    }


    @Test
    public void testSoftAssertion() throws InterruptedException {
        Thread.sleep(3000);
        SoftAssert softAssert = new SoftAssert();
        String actualTitle = page.title();
        String expectedTitle = "Selenium Practice - Student Registration Form";

        // Check if the title matches the expected value
        softAssert.assertEquals(actualTitle, expectedTitle, "Title does not match the expected value");

        // After the soft assertions, assert all to report the failures
        try {
            softAssert.assertAll();  // This will throw an exception if any soft assertion failed
            System.out.println("Test Passed: All soft assertions passed.");
        } catch (AssertionError e) {
            System.out.println("Test Failed: One or more soft assertions failed.");
            // Output any specific failure details if needed (e.g., titles or error messages)
            System.out.println("Actual Title: " + actualTitle);
            System.out.println("Expected Title: " + expectedTitle);
        }
    }

    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}