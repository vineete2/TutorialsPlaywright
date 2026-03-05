import re
import time
from datetime import datetime, timezone
from tavily import TavilyClient

TAVILY_API_KEY = ""

SEARCH_QUERIES = [
    "Test Automation Engineer Germany Selenium Playwright job 2026",
    "QA Engineer Germany Cypress TestNG job stellenangebot 2026",
    "Software Tester Automation Germany Cucumber BDD job 2026",
    "Softwaretester Automation Deutschland Selenium Playwright 2026",
    "QA Automation Engineer Berlin Hamburg Munich Cypress 2026",
    "Test Engineer Germany Appium mobile testing job 2026",
    "Quality Assurance Engineer Germany remote Playwright 2026",
    "Testautomatisierung Ingenieur Deutschland Selenium job 2026",
    "Junior QA Engineer Germany Cucumber BDD TestNG 2026",
    "Senior Test Automation Engineer Germany job 2026",
]


INCLUDE_DOMAINS = [
    # Already working
    "linkedin.com",
    "stepstone.de",
    "indeed.com",
    "indeed.de",
    "xing.com",
    "join.com",
    "greenhouse.io",
    "lever.co",
    "workwise.io",
    "stellenmarkt.de",
    "arbeitsagentur.de",
    "monster.de",
    "kimeta.de",
    "yourfirm.de",
    "jobware.de",
    "talentbait.com",
    "instaffo.com",
    "softgarden.io",
    "personio.de",
    # From the new list
    "adzuna.de",
    "careerjet.com",
    "fachinformatiker.de",
    "gigajob.com",
    "heyjobs.co",
    "joblift.de",
    "jobrapido.com",
    "jobvector.de",
    "jooble.org",
    "karriere.at",
    "meinestadt.de",
    "regiojob.de",
    "stellenanzeigen.de",
    "talent.com",
    "technik.jobs",
    "kleinanzeigen.de",
]


QA_KEYWORDS = [
    "qa", "quality assurance", "test automation", "selenium", "playwright",
    "cypress", "testng", "cucumber", "appium", "software tester",
    "qualitätssicherung", "softwaretester", "testautomatisierung",
    "test engineer", "testingenieur", "automation engineer",
    "bdd", "gherkin", "junit", "robot framework", "postman",
    "end-to-end testing", "e2e", "regression testing", "manual testing",
    "api testing", "mobile testing", "webdriver", "katalon",
    "qualitätssicherungsingenieur", "softwarequalität",
]

LISTING_PAGE_PATTERNS = re.compile(
    r'\b(\d{2,4})\s+(?:jobs?|stelle|stellenangebote|vacancies|positions)\b',
    re.IGNORECASE
)


def is_single_job_posting(title, content):
    if LISTING_PAGE_PATTERNS.search(title):
        return False
    combined = title + " " + content[:300]
    if re.search(r'search\s+\w+\s+jobs\s+in\s+germany', combined, re.IGNORECASE):
        return False
    if re.search(r'ratings?\s*&\s*salaries?', combined, re.IGNORECASE):
        return False
    # Relaxed — just return True if it passed the above checks
    return True


def fetch_tavily_jobs():
    client = TavilyClient(TAVILY_API_KEY)
    seen_urls = set()
    jobs = []
    skipped = 0

    for query in SEARCH_QUERIES:
        print(f"  🔍 Tavily: {query[:60]}...")
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=20,
                time_range="day",
                include_domains=INCLUDE_DOMAINS,
                country="germany",
            )
            time.sleep(1)

            for r in response.get("results", []):
                url = r.get("url", "").strip()
                if not url or url in seen_urls:
                    continue
                title = r.get("title", "").strip()
                content = r.get("content", "").strip()
                combined = (title + " " + content).lower()

                if not any(kw in combined for kw in QA_KEYWORDS):
                    continue
                if not re.search(
                        r'\b(?:germany|deutschland|berlin|munich|münchen|hamburg|frankfurt|köln|cologne|stuttgart|düsseldorf)\b',
                        combined, re.IGNORECASE
                ):
                    continue
                if not is_single_job_posting(title, content):
                    skipped += 1
                    continue

                seen_urls.add(url)
                jobs.append({
                    "Title":       title,
                    "Link":        url,
                    "Description": content[:2000],
                })

        except Exception as e:
            print(f"  ⚠️ Tavily error: {e}")

    print(f"\n→ {len(jobs)} jobs found, {skipped} listing pages skipped")
    return jobs


if __name__ == "__main__":
    jobs = fetch_tavily_jobs()
    print(f"\n=== Found {len(jobs)} jobs ===")
    for j in jobs:
        print(f"\n📌 {j['Title']}")
        print(f"   {j['Link']}")
        print(f"   {j['Description'][:200]}...")