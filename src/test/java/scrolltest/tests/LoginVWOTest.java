package scrolltest.tests;
//https://github.com/PramodDutta/PlaywrightJavaPOM/blob/main/src/test/java/com/scrolltest/tests/LoginVWOTest.java



import PlaywrightJavaPOM.scrolltest.pages.LoginVWOPage;
import org.testng.Assert;
import org.testng.annotations.*;



public class LoginVWOTest extends BaseTestClass {
    LoginVWOPage loginPage;

    @BeforeClass
    @Parameters({ "url", "browserName" , "headless"})
    public void browserStart(@Optional("https://app.vwo.com/#/login") String url,
                             @Optional("chrome") String browserName, @Optional("false") String headless) {
        launchPlaywright(browserName, headless);
        launchApplication(url);
    }

    @Test(priority = 1)
    @Parameters({ "username", "password" })
    public void loginTest(@Optional("zud00@heictoimage.com") String username, @Optional("TesterLogin@1457") String password) {
        loginPage = new LoginVWOPage(page);
        boolean isLoginSuccess = loginPage.login(username, password);
        Assert.assertEquals(isLoginSuccess, true);

        page.getByText("Dashboard").waitFor();
    }

    @AfterClass
    public void browserClose() {
        closePlaywright();
    }
}