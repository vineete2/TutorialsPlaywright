##  Job Scraper (Playwright CDP)

A Python-based scraper that leverages **Chrome DevTools Protocol (CDP)** to attach to your existing browser session. By "riding" inside your authenticated Chrome instance, it bypasses anti-bot measures and CORS restrictions without needing complex header spoofing.

### 🛠️ Quick Start

1.  **Install dependencies:**
    ```bash
    pip install playwright rich
    playwright install chromium
    ```
2.  **Launch Chrome in Debug Mode:**
    Run this command and log into LinkedIn/Indeed in the window that opens:
    ```bash
    & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
    ```
3.  **Run the scraper:**
    ```bash
    python job_scraper_sophia.py
    ```

### 📊 Key Features
* **CDP Connection:** Attaches via `localhost:9222` to use your real, logged-in session.
* **Smart Parsing:** Handles bilingual date formats (French/English) and filters by `MAX_DAYS_OLD`.
* **Auto-Tagging:** Extracts tech stacks (PyTest, Jenkins, etc.) directly from job titles.
* **Clean Data:** Automatic deduplication by `(title, company)` and tab-per-source isolation.

### 📁 Output
* `jobs_output.json`: Structured raw data.
* `jobs_report.html`: An interactive, searchable dashboard with keyword filtering and direct links.

---