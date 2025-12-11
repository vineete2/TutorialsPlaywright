package reportsGenerator;

import net.masterthought.cucumber.Configuration;
import net.masterthought.cucumber.ReportBuilder;

import java.io.File;
import java.util.Collections;
import java.util.List;

public class CucumberReportGenerator {

    /*
     *This is generating report
     */
    public static void main(String[] args) {
        
        File reportOutputDirectory = new File("target/cucumber-reports");
        List<String> jsonFiles = Collections.singletonList("target/cucumber.json");
        if (!jsonFile.exists()) {
        System.err.println("Required file target/cucumber.json does not exist. Please generate cucumber results before running the report generator.");
        System.exit(1);
        }
        List<String> jsonFiles = Collections.singletonList(jsonFile.getPath());
        Configuration config = new Configuration(reportOutputDirectory, "TutorialsPlaywright");
        ReportBuilder reportBuilder = new ReportBuilder(jsonFiles, config);
        reportBuilder.generateReports();
    }

}
