# 🎭 Playwright Java Tutorials

Welcome to the **Playwright Java Automation** repository!
This project contains examples and exercises for using **Playwright** with **Java** to automate browser interactions and build test frameworks.

---

## 🚀 Overview

This repository covers a variety of Playwright Java concepts, including:

* Setting up Playwright with Java
* Locators, actions, and waits
* Test structure with JUnit/TestNG
* Handling alerts, pop-ups, frames, and file uploads
* Page Object Model (POM) architecture
* Network mocking and API validation
* Parallel execution for stability
* Reporting and CI/CD integration
* Added Cucumber framework
* Job Scraper (Playwright CDP) added on 28 April 2026

##  Job Scraper (Playwright CDP)

A Python-based scraper that leverages **Chrome DevTools Protocol (CDP)** to attach to your existing browser session. By "riding" inside your authenticated Chrome instance, it bypasses anti-bot measures and CORS restrictions without needing complex header spoofing.

Located in the `/job_scraper` directory, this utility demonstrates how to use **Playwright Python** to bypass anti-bot measures by attaching to a real, authenticated Chrome session via **Chrome DevTools Protocol (CDP)**.

 🌟 Key Concept: CDP Attachment
Instead of launching a "clean" headless browser (which job boards often block), this scraper "rides" inside your already-open Chrome window using `connect_over_cdp`.
---

## 🛠️ Technologies Used

* **Java 17+**
* **Maven**
* **Playwright Java**
* **JUnit / TestNG**
* **GitHub Actions**
* **Jenkins**

---

## 📂 Sample Project Structure

```
📦 playwright-java-tutorials
 ┣ 📂 src/test/java
 ┃ ┣ 📂 day1_basics
 ┃ ┣ 📂 day2_locators
 ┃ ┣ 📂 day3_waits_assertions
 ┃ ┣ 📂 day4_test_structure
 ┃ ┣ 📂 day5_debugging
 ┃ ┣ 📂 day6_advanced_interactions
 ┃ ┣ 📂 day7_network_mocking
 ┃ ┣ 📂 day8_pom
 ┃ ┣ 📂 day9_parallel
 ┃ ┗ 📂 day10_ci_cd
 ┣ 📄 pom.xml
 ┗ 📄 README.md
```

---

## 🎉 My Thoughts

This repository demonstrates how to leverage Playwright in Java for browser automation and testing. 
It gradually introduce advanced concepts like parallel execution and CI/CD integration.
Updated Cucumber framework 
Feel free to ⭐ star the repository if you found it helpful!
---


---

Let me know if there are any improvements
