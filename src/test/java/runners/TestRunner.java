package runners;
//https://www.youtube.com/watch?v=oV32b8V4pMA&list=PLQKDzuA2cCjq29NfkM5Lpko7Dl6lhNiT6&index=6
//https://github.com/lokesh771988/PlaywrightJavaCucumberTestNG/blob/master/src/test/java/runners/TestRunner.java

import io.cucumber.testng.AbstractTestNGCucumberTests;
import io.cucumber.testng.CucumberOptions;

@CucumberOptions(
        features = "src/test/java/features",
        glue = "stepdefinitions",
        plugin = {"pretty","html:target/cucumber-reports"},
        monochrome = true

)
public class TestRunner extends AbstractTestNGCucumberTests{



}
