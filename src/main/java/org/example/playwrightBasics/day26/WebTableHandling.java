package org.example.playwrightBasics.day26;

import java.net.URISyntaxException;
import java.net.URL;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.NumberFormat;
import java.text.ParseException;
import java.util.List;

import com.microsoft.playwright.*;
import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.Test;

//src https://github.com/ebrahimhossaincse/Playwright-Tutorials-Java/tree/main/src/test/java/webtablehandling

public class WebTableHandling {
    protected static String url = "https://demo.guru99.com/test/web-table-element.php";

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
        Thread.sleep(4000);
    }

    @Test(priority = 0) //Fetch table heading
    public void fetchHeading() throws InterruptedException {
        ElementHandle tableElement = page.querySelector("//table[@class='dataTable']/thead");
        List<ElementHandle> rows = tableElement.querySelectorAll("tr");

        for (ElementHandle rowElement : rows) {
            List<ElementHandle> cells = rowElement.querySelectorAll("th");
            for (ElementHandle cellElement : cells) {
                String cellData = cellElement.textContent();
                System.out.print("| " + cellData + " |\t");
            }
            System.out.println();
        }

    }

    @Test //fetch CellValue Of Particular Row And Column
    public void fetchCellValueOfParticularRowAndColumn() throws InterruptedException{
        Thread.sleep(4000);
        // Take screenshot of the full page
        page.screenshot(new Page.ScreenshotOptions()
                .setPath(Paths.get("fullpage_screenshot.png"))
                .setFullPage(true));
        //page.querySelector("xpath=//*[@id='leftcontainer']/table/tbody/tr[3]"));

        ElementHandle tableRow = page.querySelector("//*[@id='leftcontainer']/table/tbody/tr[3]");
        String rowtext = tableRow.textContent();
        System.out.print("Third row of table : " + rowtext);

        ElementHandle cellIneed = page.querySelector("//*[@id='leftcontainer']/table/tbody/tr[3]/td[1]/a");
        String valueIneed = cellIneed.textContent();
        System.out.println("Cell value is : " + valueIneed);
    }

    @AfterSuite
    public void closeChromeBrowser() {
        page.close();
        browser.close();
        playwright.close();
    }
}