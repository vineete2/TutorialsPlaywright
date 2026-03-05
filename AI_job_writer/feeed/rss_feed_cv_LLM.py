# imports
from playwright.sync_api import sync_playwright
import requests
import csv
import io
import time
import re

# Your resume text
RESUME = """
Software Engineer with 4+ years of experience in test automation and quality assurance using Agile methodologies. MSc Computer Science graduate from Universität Paderborn. Languages: English C1, German A2, Hindi/Telugu native. Skills: Java, SQL, Selenium WebDriver, Playwright/Cypress, Postman, Jenkins, GitLab CI/CD, TestNG, Maven, Agile/Scrum. Work: Accenture 2017 - test automation frameworks, 250+ regression tests, CI/CD integration. Projects: 3D pathfinding (C++), 24/7 Fact Check (Java/Spring Boot).
"""

RSS_CSV_URL = "https://rss.app/feeds/qzt1obkq35R6dIVW.csv"
LOCAL_CSV = "jobs.csv"
OUTPUT_FILE_BASE = "skills_job"  # Base name for output files, e.g., skills_job1.tex

def fetch_and_save_jobs():
    r = requests.get(RSS_CSV_URL)
    if r.status_code != 200:
        print("Failed to download CSV.")
        exit(1)
    with open(LOCAL_CSV, "w", encoding="utf-8") as f:
        f.write(r.text)
    print("Saved jobs.csv locally.")

def get_all_jobs():
    with open(LOCAL_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def build_prompt(job, job_num):
    title = job.get('Title', 'No title')
    desc = job.get('Description', 'No description')
    link = job.get('Link', 'No link')
    return (
        "Use Fast mode (quick, concise answers only). "
        f"Hey Grok, here's my resume:\n{RESUME}\n\n"
        f"And here's a job ad (job #{job_num} in my RSS feed):\n"
        f"Title: {title}\n"
        f"Description: {desc}\n"
        f"Link: {link}\n\n"
        "Please:\n"
        "1. Analyze match (0-100 % score).\n"
        "2. Rewrite  Skills section ONLY and give output in tex format(honest, grouped by type, LaTeX-ready).\n"
        "3. New score after changes.\n"
        "No fluff, no explanations — just analysis, skills block, scores."
    )

def extract_skills_from_reply(reply_text):
    """Extract Grok's grouped skills perfectly (preserves \textbf categories)"""
    # Find the skills block after any "Rewritten Skills section..." text
    match = re.search(
        r'(?is)(?:Rewritten Skills section.*?|Skills section|Skills:)\s*[:\-]?\s*(.+?)'
        r'(?=\s*(?:New match score|after changes|Updated match score|The tweaks|\Z))',
        reply_text, re.DOTALL
    )
    if not match:
        print("Could not find skills block.")
        return None
    content = match.group(1).strip()
    # Clean up common junk at start/end
    content = re.sub(r'^\s*(honest|tailored|grouped|concise|LaTeX-ready).*?[:\-]\s*', '', content, flags=re.I)
    content = content.strip()
    # If Grok already gave LaTeX with \textbf, just wrap it
    if '\\textbf' in content or 'textbf' in content.lower():
        return '\\section*{Skills}\n' + content
    # Fallback: turn plain lines into itemize (your requested compact style)
    lines = [line.strip().rstrip('\\').strip() for line in content.split('\n') if line.strip()]
    lines = [line for line in lines if not any(x in line.lower() for x in ['match score', 'the rewrite', 'the increase'])]
    if not lines:
        return None
    latex = '\\section*{Skills}\n\\begin{itemize}[leftmargin=*,nosep]\n'
    for line in lines:
        latex += f' \\item {line}\n'
    latex += '\\end{itemize}'
    return latex

def send_to_gemini(prompt, output_file="skills.tex"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=80)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        print("Opening Gemini + handling consent...")
        # Go directly to gemini.google.com — it usually redirects to consent only on first visit
        page.goto("https://gemini.google.com/", timeout=45000)
        # Step 1: Handle consent if it appears (timeout 8 seconds)
        print("Checking for consent screen...")
        try:
            reject_btn = page.get_by_role("button", name="Reject all")
            reject_btn.wait_for(state="visible", timeout=8000)
            reject_btn.click()
            print("Clicked 'Reject all'")
            page.wait_for_load_state("networkidle")
        except:
            print("No consent screen detected (already accepted or skipped)")
        # Handle consent if it appears (non-blocking, with timeout)
       #  try:
       #      reject_btn = page.get_by_role("button", name="Reject all", timeout=10000)
       #      reject_btn.wait_for(state="visible", timeout=10000)
       #      reject_btn.click(delay=200)
       #      print("Clicked 'Reject all'")
       #      time.sleep(1.5)
       # # except PlaywrightTimeoutError:
       #      print("No consent banner appeared (or timed out) → continuing")
       # # except Exception as e:
       #      print(f"Consent handling failed: {e} → continuing anyway")
       #  # Wait for the chat input to be ready
        try:
            page.get_by_role("textbox", name="Enter a prompt for Gemini").wait_for(timeout=15000)
        except:
            print("Main textbox not found by name → will use fallback locator")
        print("Filling prompt...")
        # Reliable ways to fill the prompt (try preferred → fallback)
        prompt_filled = False
        try:
            textbox = page.get_by_role("textbox", name="Enter a prompt for Gemini")
            textbox.click()
            textbox.fill(prompt)
            prompt_filled = True
        except:
            pass
        if not prompt_filled:
            try:
                # Very common rich-textarea structure in Gemini
                page.locator("rich-textarea").locator("div").nth(1).fill(prompt)
                prompt_filled = True
            except:
                pass
        if not prompt_filled:
            # Last resort — any visible contenteditable or div with role=textbox
            page.locator('[role="textbox"], [contenteditable="true"]').first.fill(prompt)
            print("Used last-resort locator for prompt")
        print("Prompt filled")
        # Click send
        try:
            page.get_by_role("button", name="Send message").click(delay=150)
            print("Message sent")
        except:
            # Fallback: usually the send button is the only button with Send icon or near the textarea
            page.locator('button:has(svg)').last.click()  # risky but often works
            print("Used fallback send button locator")
        print("Waiting for Gemini reply...")
        # === Smart polling for the latest response ===
        reply_text = None
        start = time.time()
        while time.time() - start < 60:  # max wait 60s
            time.sleep(1.8)
            # Preferred: last message container that contains markdown (very reliable in 2025–2026)
            last_reply = page.locator(
                'div.markdown, '
                'div[role="presentation"] div.markdown, '
                '[data-message-author-role="model"] div.markdown'
            ).last
            if last_reply.is_visible():
                reply_text = last_reply.inner_text().strip()
                if len(reply_text) > 80:  # heuristic: real answer is longer than placeholder
                    break
            # Fallback 1: any recent model response block with randomized id prefix
            try:
                model_responses = page.locator('[id^="model-response-message-contentr_"]')
                if model_responses.count() > 0:
                    last_model = model_responses.last
                    if last_model.is_visible():
                        reply_text = last_model.inner_text().strip()
                        if len(reply_text) > 80:
                            break
            except:
                pass
        if reply_text:
            print("\n=== GEMINI REPLY ===\n")
            print(reply_text)
            # Your existing extraction logic
            skills = extract_skills_from_reply(reply_text)  # ← your function
            if skills:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(skills)
                print(f"\n✅ Saved clean LaTeX Skills to: {output_file}")
            else:
                with open("../full_reply.txt", "w", encoding="utf-8") as f:
                    f.write(reply_text)
                print("Skills block not found — full reply saved to full_reply.txt")
        else:
            print("Could not reliably capture the reply after 60s.")
            print("→ Please copy it manually from the browser.")
        page.pause()  # lets you inspect
        input("\nPress Enter to close browser...")
        browser.close()

# Other functions like send_to_gemini_old, send_to_gemini_sample, send_to_grok can remain as is

if __name__ == "__main__":
    fetch_and_save_jobs()
    jobs = get_all_jobs()
    print(f"Found {len(jobs)} jobs. Processing all...")
    for i, job in enumerate(jobs):
        job_num = i + 1
        prompt = build_prompt(job, job_num)
        output_file = f"{OUTPUT_FILE_BASE}{job_num}.tex"
        print(f"\nProcessing job #{job_num}: {job.get('Title', 'Untitled')}")
        send_to_gemini(prompt, output_file=output_file)
        time.sleep(5)  # Short delay between jobs to avoid overwhelming the browser/service