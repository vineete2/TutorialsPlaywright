"""
=============================================================================
  QA / Software Testing Job Scraper — Sophia Antipolis & Nice
  Uses Playwright CDP to connect to YOUR already-open Chrome session.
  This bypasses all anti-bot / CORS / login walls completely.
=============================================================================

SETUP (one-time):
  1. Install deps:
       pip install playwright rich requests
       playwright install chromium

  2. Launch Chrome with remote debugging ON:
       Windows:
         "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\chrome-debug"
       Mac:
         /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome
             --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
       Linux:
         google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug

  3. In that Chrome window, log into:
       - linkedin.com
       - fr.indeed.com
       (Glassdoor, HelloWork, Welcome to the Jungle work without login)

  4. Run:
       python job_scraper_sophia.py

  Output:
       - jobs_output.json   — raw structured data
       - jobs_report.html   — clickable HTML report you can open in browser
=============================================================================
"""

import json
import time
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("❌ playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

CDP_URL       = "http://localhost:9222"   # Chrome debug port
MAX_DAYS_OLD  = 14                        # only jobs posted within N days
PAUSE         = 1.8                       # seconds between actions (be polite)
OUTPUT_JSON   = "jobs_output.json"
OUTPUT_HTML   = "jobs_report.html"

KEYWORDS_EN   = "QA software testing test automation quality assurance"
KEYWORDS_FR   = "ingénieur test QA automatisation testeur logiciel"
LOCATION_MAIN = "Sophia Antipolis"
LOCATION_ALT  = "Nice"

console = Console() if HAS_RICH else None

def log(msg, style=""):
    if HAS_RICH:
        console.print(f"  {msg}", style=style or "")
    else:
        print(f"  {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# DATE PARSING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def parse_relative_date(text: str) -> datetime | None:
    """Turn 'Il y a 3 jours', '2 days ago', 'heute', 'Posted 5 days ago' → datetime."""
    if not text:
        return None
    text = text.lower().strip()
    today = datetime.now()

    patterns = [
        # English
        (r'(\d+)\s*hour',    lambda n: today - timedelta(hours=int(n))),
        (r'(\d+)\s*day',     lambda n: today - timedelta(days=int(n))),
        (r'(\d+)\s*week',    lambda n: today - timedelta(weeks=int(n))),
        (r'(\d+)\s*month',   lambda n: today - timedelta(days=int(n)*30)),
        (r'just now|today|aujourd\'hui|heute', lambda n: today),
        (r'yesterday|hier|gestern', lambda n: today - timedelta(days=1)),
        # French
        (r'(\d+)\s*heure',   lambda n: today - timedelta(hours=int(n))),
        (r'(\d+)\s*jour',    lambda n: today - timedelta(days=int(n))),
        (r'(\d+)\s*semaine', lambda n: today - timedelta(weeks=int(n))),
        (r'(\d+)\s*mois',    lambda n: today - timedelta(days=int(n)*30)),
        # "30+" days — treat as too old
        (r'30\+|plus de 30', lambda n: today - timedelta(days=31)),
    ]

    for pattern, calc in patterns:
        m = re.search(pattern, text)
        if m:
            n = m.group(1) if m.lastindex else None
            try:
                return calc(n)
            except Exception:
                return None
    return None


def is_within_days(date_obj: datetime | None, days: int = MAX_DAYS_OLD) -> bool:
    if date_obj is None:
        return True   # keep if we can't parse — better to show than miss
    return (datetime.now() - date_obj).days <= days


# ─────────────────────────────────────────────────────────────────────────────
# SCRAPER BASE
# ─────────────────────────────────────────────────────────────────────────────

class JobScraper:
    def __init__(self, page):
        self.page = page
        self.jobs = []

    def safe_text(self, el, selector, default=""):
        try:
            return el.query_selector(selector).inner_text().strip()
        except Exception:
            return default

    def safe_attr(self, el, selector, attr, default=""):
        try:
            return el.query_selector(selector).get_attribute(attr) or default
        except Exception:
            return default

    def scroll_to_bottom(self, steps=5):
        for _ in range(steps):
            self.page.keyboard.press("End")
            time.sleep(0.6)


# ─────────────────────────────────────────────────────────────────────────────
# INDEED FR SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

class IndeedScraper(JobScraper):
    SOURCE = "Indeed FR"

    def scrape(self, keywords=KEYWORDS_FR, location=LOCATION_MAIN, max_pages=3):
        log(f"[bold cyan]→ Indeed FR[/bold cyan] | {keywords[:40]}... | {location}")
        enc_kw  = keywords.replace(" ", "+")
        enc_loc = location.replace(" ", "+")
        # fromage=14 = posted in last 14 days, sort=date = newest first
        url = (f"https://fr.indeed.com/jobs?q={enc_kw}&l={enc_loc}"
               f"&fromage={MAX_DAYS_OLD}&sort=date")

        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(PAUSE)
        except PWTimeout:
            log("  ⚠ Indeed timed out", "yellow")
            return []

        jobs_found = []
        for page_num in range(max_pages):
            self.scroll_to_bottom(3)
            cards = self.page.query_selector_all("div.job_seen_beacon, div.resultContent")
            log(f"  Page {page_num+1}: {len(cards)} cards")

            for card in cards:
                try:
                    title    = self.safe_text(card, "h2.jobTitle a span, h2.jobTitle span")
                    company  = self.safe_text(card, "[data-testid='company-name'], .companyName")
                    location_txt = self.safe_text(card, "[data-testid='text-location'], .companyLocation")
                    date_txt = self.safe_text(card, "[data-testid='myJobsStateDate'], .date, span.date")
                    link_el  = card.query_selector("h2.jobTitle a, a.jcs-JobTitle")
                    href     = link_el.get_attribute("href") if link_el else ""
                    if href and not href.startswith("http"):
                        href = "https://fr.indeed.com" + href

                    if not title:
                        continue

                    parsed_date = parse_relative_date(date_txt)
                    if not is_within_days(parsed_date):
                        continue

                    jobs_found.append({
                        "title":    title,
                        "company":  company,
                        "location": location_txt or location,
                        "date_raw": date_txt,
                        "date":     parsed_date.isoformat() if parsed_date else None,
                        "url":      href,
                        "source":   self.SOURCE,
                        "tags":     [],
                    })
                except Exception:
                    continue

            # Next page
            next_btn = self.page.query_selector("a[data-testid='pagination-page-next'], a[aria-label='Next Page']")
            if next_btn and page_num < max_pages - 1:
                next_btn.click()
                time.sleep(PAUSE * 1.5)
            else:
                break

        self.jobs.extend(jobs_found)
        log(f"  ✓ {len(jobs_found)} jobs from Indeed FR ({location})", "green")
        return jobs_found


# ─────────────────────────────────────────────────────────────────────────────
# LINKEDIN SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

class LinkedInScraper(JobScraper):
    SOURCE = "LinkedIn"

    def scrape(self, keywords="QA engineer software testing", location=LOCATION_MAIN, max_pages=3):
        log(f"[bold blue]→ LinkedIn[/bold blue] | {keywords[:40]}... | {location}")
        enc_kw  = keywords.replace(" ", "%20")
        enc_loc = location.replace(" ", "%20")
        # f_TPR=r1209600 = past 14 days (14*86400=1209600 seconds)
        url = (f"https://www.linkedin.com/jobs/search/?keywords={enc_kw}"
               f"&location={enc_loc}&f_TPR=r{MAX_DAYS_OLD * 86400}&sortBy=DD")

        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(PAUSE)
        except PWTimeout:
            log("  ⚠ LinkedIn timed out", "yellow")
            return []

        jobs_found = []
        seen_urls  = set()

        for page_num in range(max_pages):
            # Scroll to load lazy-rendered cards
            for _ in range(8):
                self.page.keyboard.press("End")
                time.sleep(0.5)

            cards = self.page.query_selector_all(
                "li.jobs-search-results__list-item, "
                "div.base-card, "
                "li.job-search-card"
            )
            log(f"  Page {page_num+1}: {len(cards)} cards")

            for card in cards:
                try:
                    title    = self.safe_text(card, "h3, h3.base-search-card__title, .job-card-list__title")
                    company  = self.safe_text(card, "h4, h4.base-search-card__subtitle, .job-card-container__primary-description")
                    location_txt = self.safe_text(card, "span.job-search-card__location, .job-card-container__metadata-item")
                    date_txt = self.safe_text(card, "time, .job-search-card__listdate, .job-card-container__listed-status")
                    time_el  = card.query_selector("time")
                    if time_el:
                        date_txt = time_el.get_attribute("datetime") or date_txt

                    link_el  = card.query_selector("a.base-card__full-link, a.job-card-list__title, a")
                    href     = link_el.get_attribute("href") if link_el else ""

                    if not title or href in seen_urls:
                        continue
                    seen_urls.add(href)

                    parsed_date = parse_relative_date(date_txt)
                    if not is_within_days(parsed_date):
                        continue

                    jobs_found.append({
                        "title":    title,
                        "company":  company,
                        "location": location_txt or location,
                        "date_raw": date_txt,
                        "date":     parsed_date.isoformat() if parsed_date else None,
                        "url":      href,
                        "source":   self.SOURCE,
                        "tags":     [],
                    })
                except Exception:
                    continue

            # LinkedIn pagination — click next or "See more jobs"
            see_more = self.page.query_selector("button.infinite-scroller__show-more-button, button[aria-label*='next']")
            if see_more and page_num < max_pages - 1:
                see_more.click()
                time.sleep(PAUSE * 1.5)
            else:
                break

        self.jobs.extend(jobs_found)
        log(f"  ✓ {len(jobs_found)} jobs from LinkedIn ({location})", "green")
        return jobs_found


# ─────────────────────────────────────────────────────────────────────────────
# GLASSDOOR SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

class GlassdoorScraper(JobScraper):
    SOURCE = "Glassdoor"

    def scrape(self):
        log("[bold green]→ Glassdoor[/bold green] | test engineer | Antibes area")
        # Antibes city code covers Sophia Antipolis area
        url = ("https://www.glassdoor.com/Job/antibes-test-engineer-jobs-"
               "SRCH_IL.0,7_IC3032458_KO8,21.htm?fromAge=14&sortBy=date_desc")
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(PAUSE)
        except PWTimeout:
            log("  ⚠ Glassdoor timed out", "yellow")
            return []

        self.scroll_to_bottom(5)
        jobs_found = []

        cards = self.page.query_selector_all(
            "li.react-job-listing, article.job-search-results_JobCard__container__oTeE2, "
            "div[data-test='job-search-results-job-listing']"
        )
        log(f"  {len(cards)} cards")

        for card in cards:
            try:
                title    = self.safe_text(card, "a[data-test='job-title'], .job-title, h3")
                company  = self.safe_text(card, "[data-test='employer-name'], .employer-name, h4")
                location_txt = self.safe_text(card, "[data-test='emp-location'], .location, .job-location")
                date_txt = self.safe_text(card, "[data-test='job-age'], .listing-age, time")
                link_el  = card.query_selector("a[data-test='job-title'], a.jobLink, a")
                href     = link_el.get_attribute("href") if link_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.glassdoor.com" + href

                if not title:
                    continue

                parsed_date = parse_relative_date(date_txt)
                if not is_within_days(parsed_date):
                    continue

                jobs_found.append({
                    "title":    title,
                    "company":  company,
                    "location": location_txt or "Antibes/Sophia Antipolis area",
                    "date_raw": date_txt,
                    "date":     parsed_date.isoformat() if parsed_date else None,
                    "url":      href,
                    "source":   self.SOURCE,
                    "tags":     [],
                })
            except Exception:
                continue

        self.jobs.extend(jobs_found)
        log(f"  ✓ {len(jobs_found)} jobs from Glassdoor", "green")
        return jobs_found


# ─────────────────────────────────────────────────────────────────────────────
# WELCOME TO THE JUNGLE SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

class WelcomeJungleScraper(JobScraper):
    SOURCE = "Welcome to the Jungle"

    def scrape(self):
        log("[bold magenta]→ Welcome to the Jungle[/bold magenta] | QA test automation | Sophia")
        url = ("https://www.welcometothejungle.com/fr/jobs?"
               "refinementList%5Boffice.country_code%5D%5B%5D=FR"
               "&query=QA+test+automation&aroundQuery=Sophia+Antipolis%2C+France"
               "&aroundRadius=30000")
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(PAUSE * 1.5)
        except PWTimeout:
            log("  ⚠ Welcome to the Jungle timed out", "yellow")
            return []

        self.scroll_to_bottom(6)
        jobs_found = []

        cards = self.page.query_selector_all(
            "li[data-testid='search-results-list-item-wrapper'], "
            "article.sc-5hsVqn, "
            "div[class*='JobCard']"
        )
        log(f"  {len(cards)} cards")

        for card in cards:
            try:
                title    = self.safe_text(card, "h4, h3, [data-testid='job-title'], strong")
                company  = self.safe_text(card, "p, [data-testid='company-name'], span.company")
                location_txt = self.safe_text(card, "[data-testid='job-location'], span.location, i+span")
                date_txt = self.safe_text(card, "time, [data-testid='job-date'], span.date")
                link_el  = card.query_selector("a")
                href     = link_el.get_attribute("href") if link_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.welcometothejungle.com" + href

                if not title:
                    continue

                parsed_date = parse_relative_date(date_txt)
                if not is_within_days(parsed_date):
                    continue

                jobs_found.append({
                    "title":    title,
                    "company":  company,
                    "location": location_txt or "Sophia Antipolis area",
                    "date_raw": date_txt,
                    "date":     parsed_date.isoformat() if parsed_date else None,
                    "url":      href,
                    "source":   self.SOURCE,
                    "tags":     [],
                })
            except Exception:
                continue

        self.jobs.extend(jobs_found)
        log(f"  ✓ {len(jobs_found)} jobs from Welcome to the Jungle", "green")
        return jobs_found


# ─────────────────────────────────────────────────────────────────────────────
# HELLOWORK SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

class HelloWorkScraper(JobScraper):
    SOURCE = "HelloWork"

    def scrape(self):
        log("[bold yellow]→ HelloWork[/bold yellow] | ingénieur test QA | Sophia Antipolis")
        url = ("https://www.hellowork.com/fr-fr/emplois/recherche.html?"
               "k=ing%C3%A9nieur+test+QA&l=Sophia-Antipolis-06560&d=14")
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(PAUSE)
        except PWTimeout:
            log("  ⚠ HelloWork timed out", "yellow")
            return []

        self.scroll_to_bottom(4)
        jobs_found = []

        cards = self.page.query_selector_all(
            "article.tw-relative, "
            "li[data-cy='job-item'], "
            "article[data-cy='job-card']"
        )
        log(f"  {len(cards)} cards")

        for card in cards:
            try:
                title    = self.safe_text(card, "h2 a, h3 a, [data-cy='job-title']")
                company  = self.safe_text(card, "[data-cy='company-name'], .company, span.font-semibold")
                location_txt = self.safe_text(card, "[data-cy='job-location'], span.location")
                date_txt = self.safe_text(card, "time, [data-cy='job-date'], span.date, .tw-text-xs")
                link_el  = card.query_selector("h2 a, h3 a, a")
                href     = link_el.get_attribute("href") if link_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.hellowork.com" + href

                if not title:
                    continue

                parsed_date = parse_relative_date(date_txt)
                if not is_within_days(parsed_date):
                    continue

                jobs_found.append({
                    "title":    title,
                    "company":  company,
                    "location": location_txt or "Sophia Antipolis",
                    "date_raw": date_txt,
                    "date":     parsed_date.isoformat() if parsed_date else None,
                    "url":      href,
                    "source":   self.SOURCE,
                    "tags":     [],
                })
            except Exception:
                continue

        self.jobs.extend(jobs_found)
        log(f"  ✓ {len(jobs_found)} jobs from HelloWork", "green")
        return jobs_found


# ─────────────────────────────────────────────────────────────────────────────
# DEDUP + ENRICH
# ─────────────────────────────────────────────────────────────────────────────

QA_KEYWORDS = [
    "QA", "test", "testing", "qualité", "quality", "automation", "automatisation",
    "selenium", "pytest", "robot framework", "jenkins", "jira", "sdet", "testeur",
    "validation", "istqb", "appium", "playwright", "cypress", "non-regression"
]

def is_qa_job(job: dict) -> bool:
    text = (job.get("title", "") + " " + " ".join(job.get("tags", []))).lower()
    return any(kw.lower() in text for kw in QA_KEYWORDS)

def extract_tags(title: str) -> list[str]:
    tag_map = {
        "selenium": "Selenium", "pytest": "PyTest", "python": "Python",
        "java": "Java", "javascript": "JavaScript", "robot framework": "Robot Framework",
        "jenkins": "Jenkins", "jira": "Jira", "docker": "Docker",
        "agile": "Agile", "scrum": "Scrum", "devops": "DevOps",
        "playwright": "Playwright", "cypress": "Cypress", "appium": "Appium",
        "ios": "iOS", "android": "Android", "embedded": "Embedded",
        "istqb": "ISTQB", "automation": "Automation", "automatisation": "Automation",
        "mobile": "Mobile", "healthcare": "Healthcare", "automotive": "Automotive",
        "ci/cd": "CI/CD", "git": "Git", "api": "API testing",
    }
    title_lower = title.lower()
    return [v for k, v in tag_map.items() if k in title_lower]

def dedup_and_enrich(jobs: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for job in jobs:
        key = (job["title"].lower().strip(), job["company"].lower().strip())
        if key in seen:
            continue
        seen.add(key)
        job["tags"] = extract_tags(job["title"])
        result.append(job)
    result.sort(key=lambda j: j.get("date") or "", reverse=True)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# HTML REPORT GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

SOURCE_COLORS = {
    "Indeed FR":             ("#1a56ab", "#e7f0fa"),
    "LinkedIn":              ("#0a66c2", "#e8f3fb"),
    "Glassdoor":             ("#0caa41", "#e8f5e9"),
    "Welcome to the Jungle": ("#d4520a", "#fff0e6"),
    "HelloWork":             ("#7c3aed", "#f3e8ff"),
}

def generate_html_report(jobs: list[dict], output_path: str):
    now = datetime.now().strftime("%d %B %Y, %H:%M")
    rows = ""
    for j in jobs:
        sc, bg = SOURCE_COLORS.get(j["source"], ("#555", "#f0f0f0"))
        tags_html = " ".join(
            f'<span style="background:#f0f0f0;color:#444;font-size:11px;padding:2px 7px;border-radius:4px;">{t}</span>'
            for t in j.get("tags", [])
        )
        date_display = j.get("date_raw") or "unknown"
        url = j.get("url") or "#"
        rows += f"""
        <tr>
          <td style="padding:12px 14px;">
            <a href="{url}" target="_blank" style="font-weight:600;color:#111;text-decoration:none;font-size:14px;">{j['title']}</a>
            <div style="margin-top:4px;">{tags_html}</div>
          </td>
          <td style="padding:12px 14px;font-size:13px;color:#333;white-space:nowrap;">{j['company']}</td>
          <td style="padding:12px 14px;font-size:12px;color:#666;">{j['location']}</td>
          <td style="padding:12px 14px;font-size:11px;white-space:nowrap;">
            <span style="background:{bg};color:{sc};padding:3px 9px;border-radius:4px;font-weight:600;">{j['source']}</span>
          </td>
          <td style="padding:12px 14px;font-size:12px;color:#888;white-space:nowrap;">{date_display}</td>
          <td style="padding:12px 14px;">
            <a href="{url}" target="_blank"
               style="font-size:11px;padding:4px 12px;border:1px solid #ddd;border-radius:5px;text-decoration:none;color:#333;background:#fff;">
              Open ↗
            </a>
          </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QA Jobs — Sophia Antipolis & Nice ({now})</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: #f7f8fa; color: #111; padding: 2rem; }}
  h1 {{ font-size: 22px; font-weight: 700; margin-bottom: 4px; }}
  .sub {{ font-size: 13px; color: #666; margin-bottom: 1.5rem; }}
  .stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 1.5rem; }}
  .stat {{ background: #fff; border: 1px solid #e8e8e8; border-radius: 10px;
           padding: 14px 20px; min-width: 120px; }}
  .stat-n {{ font-size: 28px; font-weight: 700; }}
  .stat-l {{ font-size: 11px; color: #888; margin-top: 2px; }}
  .controls {{ display: flex; gap: 10px; margin-bottom: 1rem; flex-wrap: wrap; }}
  input, select {{ padding: 8px 12px; border: 1px solid #ddd; border-radius: 7px;
                   font-size: 13px; outline: none; }}
  input {{ min-width: 220px; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff;
           border: 1px solid #e8e8e8; border-radius: 12px; overflow: hidden;
           box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  thead tr {{ background: #f4f5f7; }}
  th {{ padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 700;
        color: #888; text-transform: uppercase; letter-spacing: 0.04em;
        border-bottom: 1px solid #e8e8e8; }}
  tr {{ border-bottom: 1px solid #f0f0f0; }}
  tr:last-child {{ border-bottom: none; }}
  tr:hover {{ background: #fafafa; }}
  .footer {{ margin-top: 1.5rem; font-size: 11px; color: #aaa; }}
  #filter {{ width: 300px; }}
</style>
</head>
<body>

<h1>QA &amp; Software Testing Jobs</h1>
<div class="sub">Sophia Antipolis &amp; Nice area · Posted within {MAX_DAYS_OLD} days · Scraped {now}</div>

<div class="stats">
  <div class="stat"><div class="stat-n">{len(jobs)}</div><div class="stat-l">Total jobs</div></div>
  <div class="stat"><div class="stat-n">{len(set(j['company'] for j in jobs))}</div><div class="stat-l">Companies</div></div>
  <div class="stat"><div class="stat-n">{len(set(j['source'] for j in jobs))}</div><div class="stat-l">Sources</div></div>
</div>

<div class="controls">
  <input id="filter" type="text" placeholder="Filter by title, company, tag..." oninput="filterTable()" />
  <select id="src-filter" onchange="filterTable()">
    <option value="">All sources</option>
    {''.join(f'<option value="{s}">{s}</option>' for s in set(j["source"] for j in jobs))}
  </select>
</div>

<table id="job-table">
  <thead>
    <tr>
      <th>Title &amp; Tags</th><th>Company</th><th>Location</th>
      <th>Source</th><th>Posted</th><th>Link</th>
    </tr>
  </thead>
  <tbody id="tbody">
    {rows}
  </tbody>
</table>

<div class="footer">
  Links open original job postings. Scraped via Playwright CDP from your Chrome session.
</div>

<script>
function filterTable() {{
  const q   = document.getElementById('filter').value.toLowerCase();
  const src = document.getElementById('src-filter').value.toLowerCase();
  const rows = document.querySelectorAll('#tbody tr');
  rows.forEach(r => {{
    const text = r.innerText.toLowerCase();
    const show = (!q || text.includes(q)) && (!src || text.includes(src));
    r.style.display = show ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    log(f"  ✓ HTML report saved → {output_path}", "green")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if HAS_RICH:
        console.rule("[bold]QA Job Scraper — Sophia Antipolis & Nice[/bold]")
    else:
        print("=" * 60)
        print("  QA Job Scraper — Sophia Antipolis & Nice")
        print("=" * 60)

    log(f"Connecting to Chrome via CDP at {CDP_URL}...")

    all_jobs = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            log(f"❌ Cannot connect to Chrome CDP: {e}", "bold red")
            log("")
            log("Make sure Chrome is running with:", "yellow")
            log('  chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\\\chrome-debug"', "yellow")
            sys.exit(1)

        context = browser.contexts[0]
        log("✓ Connected to Chrome!", "green")

        def get_fresh_tab():
            """Open a new blank tab for each scraper to avoid cookie/state bleed."""
            page = context.new_page()
            page.set_default_timeout(15000)
            return page

        # ── Indeed FR (Sophia Antipolis)
        page = get_fresh_tab()
        scraper = IndeedScraper(page)
        scraper.scrape(keywords=KEYWORDS_FR, location=LOCATION_MAIN)
        all_jobs.extend(scraper.jobs)
        page.close()
        time.sleep(PAUSE)

        # ── Indeed FR (Nice)
        page = get_fresh_tab()
        scraper = IndeedScraper(page)
        scraper.scrape(keywords=KEYWORDS_FR, location=LOCATION_ALT)
        all_jobs.extend(scraper.jobs)
        page.close()
        time.sleep(PAUSE)

        # ── Indeed FR (English keywords)
        page = get_fresh_tab()
        scraper = IndeedScraper(page)
        scraper.scrape(keywords=KEYWORDS_EN, location=LOCATION_MAIN)
        all_jobs.extend(scraper.jobs)
        page.close()
        time.sleep(PAUSE)

        # ── LinkedIn
        page = get_fresh_tab()
        scraper = LinkedInScraper(page)
        scraper.scrape(keywords="QA engineer software testing automation", location=LOCATION_MAIN)
        all_jobs.extend(scraper.jobs)
        scraper.scrape(keywords="ingénieur test qualité logiciel", location=LOCATION_ALT)
        all_jobs.extend(scraper.jobs)
        page.close()
        time.sleep(PAUSE)

        # ── Glassdoor
        page = get_fresh_tab()
        scraper = GlassdoorScraper(page)
        scraper.scrape()
        all_jobs.extend(scraper.jobs)
        page.close()
        time.sleep(PAUSE)

        # ── Welcome to the Jungle
        page = get_fresh_tab()
        scraper = WelcomeJungleScraper(page)
        scraper.scrape()
        all_jobs.extend(scraper.jobs)
        page.close()
        time.sleep(PAUSE)

        # ── HelloWork
        page = get_fresh_tab()
        scraper = HelloWorkScraper(page)
        scraper.scrape()
        all_jobs.extend(scraper.jobs)
        page.close()

    # ── Dedup, enrich, filter QA-only
    clean = dedup_and_enrich(all_jobs)
    clean = [j for j in clean if is_qa_job(j)]

    log("")
    log(f"Total raw collected : {len(all_jobs)}", "cyan")
    log(f"After dedup + filter: [bold]{len(clean)}[/bold] QA jobs within {MAX_DAYS_OLD} days", "cyan")
    log("")

    # ── Save JSON
    Path(OUTPUT_JSON).write_text(json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"JSON saved → {OUTPUT_JSON}", "green")

    # ── Save HTML
    generate_html_report(clean, OUTPUT_HTML)

    # ── Console table
    if HAS_RICH:
        t = Table(show_header=True, header_style="bold", show_lines=True)
        t.add_column("Title", style="bold", max_width=42)
        t.add_column("Company", max_width=22)
        t.add_column("Source", max_width=18)
        t.add_column("Posted", max_width=14)
        t.add_column("URL", max_width=50)
        for j in clean[:30]:
            t.add_row(j["title"], j["company"], j["source"], j.get("date_raw",""), j["url"])
        console.print(t)
        if len(clean) > 30:
            console.print(f"  ... and {len(clean)-30} more in {OUTPUT_HTML}")
    else:
        print(f"\n{'#':>3}  {'Title':<45} {'Company':<25} {'Source':<22} Posted")
        print("-" * 110)
        for i, j in enumerate(clean, 1):
            print(f"{i:>3}. {j['title'][:44]:<45} {j['company'][:24]:<25} {j['source'][:21]:<22} {j.get('date_raw','')}")

    log("")
    log(f"✅ Done! Open [bold]{OUTPUT_HTML}[/bold] in your browser for the full clickable report.", "bold green")


if __name__ == "__main__":
    main()
