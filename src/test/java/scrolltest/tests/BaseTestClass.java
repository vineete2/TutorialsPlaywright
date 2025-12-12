package scrolltest.tests;
import com.microsoft.playwright.*;
import com.microsoft.playwright.options.WaitUntilState;

public class BaseTestClass {

    Playwright playwright;
    BrowserType browserType;
    Browser browser;
    BrowserContext context;
    protected Page page;

    public void launchPlaywright(String browserName, String headless) {
        playwright = Playwright.create();
        if (browserName.equalsIgnoreCase("chrome") || browserName.equalsIgnoreCase("msedge")
                || browserName.equalsIgnoreCase("chromium")) {
            browserType = playwright.chromium();
        } else if (browserName.equalsIgnoreCase("webkit")) {
            browserType = playwright.webkit();
        }
        if (headless.equalsIgnoreCase("true")) {
            browser = browserType.launch(new BrowserType.LaunchOptions().setChannel(browserName).setHeadless(true));
        } else {
            browser = browserType.launch(new BrowserType.LaunchOptions().setChannel(browserName).setHeadless(false));
        }
        context = browser.newContext(new Browser.NewContextOptions().setViewportSize(1400, 700));
        page = context.newPage();
        //page = browser.newPage();
        System.out.println("**** Project Browser Name and Version is : " + browserName + " : " + browser.version());
    }

    public void launchApplication(String url) {
        page.navigate(url, new Page.NavigateOptions().setWaitUntil(WaitUntilState.NETWORKIDLE));
        //page.getByText("Dashboard").waitFor();
        //page.waitForSelector(String.valueOf(page.getByText("Dashboard")));
    }

    public void closePlaywright() {
        page.close();
        browser.close();
        playwright.close();
    }

}