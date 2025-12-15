package scrolltest.todo;

import com.microsoft.playwright.*;

public class JSHandles {

    public static void main(String[] args) throws InterruptedException {
        try (Playwright playwright = Playwright.create()) {
            Browser browser = playwright.chromium().launch(new BrowserType.LaunchOptions().setHeadless(false).setSlowMo(200));
            Page page = browser.newPage();
            page.navigate("https://vwo.com/free-trial/");
            Thread.sleep(5000);
            JSHandle windowHandle = page.evaluateHandle("window._vwo_pc_custom");
            JSHandle windowHandle2 = page.evaluateHandle("window.scrollTo(0, 344);");
            System.out.println(windowHandle.jsonValue());

        }
    }
}