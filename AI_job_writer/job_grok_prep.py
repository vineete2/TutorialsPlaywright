import requests
import csv
import io

# Your resume text (cleaned from LaTeX - paste this once)
RESUME = """
Software Engineer with 4+ years of experience in test automation and quality assurance using Agile methodologies. 
MSc Computer Science graduate from Universität Paderborn.
Languages: English C1, German A2, Hindi/Telugu native.
Skills: Java, SQL, Selenium WebDriver, Playwright/Cypress, Postman, Jenkins, GitLab CI/CD, TestNG, Maven, Agile/Scrum.
Work: Accenture 2017 - test automation frameworks, 250+ regression tests, CI/CD integration.
Projects: 3D pathfinding (C++), 24/7 Fact Check (Java/Spring Boot).
"""

RSS_CSV_URL = "https://rss.app/feeds/qzt1obkq35R6dIVW.csv"

def main():
    # Download CSV
    response = requests.get(RSS_CSV_URL)
    if response.status_code != 200:
        print("Failed to fetch RSS CSV. Check the URL.")
        return

    # Read as CSV
    csv_data = io.StringIO(response.text)
    reader = csv.DictReader(csv_data)

    jobs = list(reader)
    if not jobs:
        print("No jobs found in CSV.")
        return

    # Take FIRST job only
    first_job = jobs[0]
    title = first_job.get('title', 'No title')
    desc = first_job.get('description', 'No description')
    link = first_job.get('link', 'No link')

    # Build prompt for Grok
    prompt = f"""
Hey Grok, here's my resume:
{RESUME}

And here's a job ad:
Title: {title}
Description: {desc}
Link: {link}

Please:
1. Analyze how well my profile matches this job (give a % score, 0-100).
2. Rewrite ONLY my Skills section to better fit this job - keep it honest, concise, copy-paste ready for LaTeX/Word.
3. Tell me the new match score after changes.
"""

    print("=== COPY THIS TO GROK ===\n")
    print(prompt)
    print("\n=== END OF PROMPT ===")
    print(f"\nJob used: {title}")
    print(f"Total jobs in feed: {len(jobs)}")

if __name__ == "__main__":
    main()