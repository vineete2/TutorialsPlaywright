package pages;

import com.microsoft.playwright.Page;

public class DashboardPage {
    private Page page;

    public DashboardPage(Page page) {
        this.page = page;
    }

    private String allLabels = ".oxd-main-menu-item";

}