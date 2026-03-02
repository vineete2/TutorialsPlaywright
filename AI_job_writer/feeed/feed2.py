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
OUTPUT_FILE_BASE = "skills_job"  # Base name for output files, e.g., skills_job_Company_1.tex

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

def extract_company(title):
    match = re.match(r"^(.*?)(?: sucht|hiring) ", title, re.IGNORECASE)
    if match:
        company = match.group(1).strip()
        company = re.sub(r'[^\w\-]', '_', company)
        company = re.sub(r'_+', '_', company).strip('_')
        return company
    return "unknown"

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
        "2. Rewrite ONLY Skills section in tex file format (honest, grouped by type, LaTeX-ready). "
        "Format each skill group as: \\textbf{Label:} value value value \\\\ "
        "where \\textbf{} wraps ONLY the label before the colon, NOT the entire line. "
        "Do NOT add a 'Technical Skills' sub-header or any subsection inside the Skills block. "
        "Do NOT include a Languages entry in the Skills section — languages are listed separately elsewhere in the CV.\n"
        "3. New score after changes.\n"
        "No fluff, no explanations — just analysis, skills block, scores."
    )

def remove_languages_from_skills(skills_block):
    """Remove any Languages line from inside the skills itemize block."""
    lang_patterns = [
        r'\\item\s*\\textbf\{[^}]*[Ll]anguages[^}]*\}[:\s]*.*?(?=\\item|\\end\{itemize\})',
        r'\\item\s*English\s*[\(\[].*?[\)\]].*?(?=\\item|\\end\{itemize\})',
        r'\s*\\textbf\{[Ll]anguages[^}]*\}[:\s]*[^\\\n]*(?:\\\\)?',
    ]
    for pat in lang_patterns:
        skills_block = re.sub(pat, '', skills_block, flags=re.I | re.DOTALL)
    return skills_block

def clean_skills_block(skills_block):
    """
    Fix two common Gemini formatting issues:
    1. Remove 'Technical Skills' sub-header (subsection or bold line inside Skills).
    2. Ensure \textbf{} only wraps the label (e.g. 'Testing & QA:'), not the full line.
       Pattern Gemini produces:  \textbf{Label: value value value} \\
       Pattern we want:          \textbf{Label:} value value value \\
    """
    # 1. Remove \textbf{Technical Skills} or \subsection*{Technical Skills} lines entirely
    skills_block = re.sub(
        r'(?m)^\s*(?:\\subsection\*?\s*\{Technical Skills\}|\\textbf\{Technical Skills\})\s*\\?\s*$',
        '',
        skills_block,
        flags=re.I
    )
    # Also remove bare "Technical Skills" lines (no LaTeX command)
    skills_block = re.sub(r'(?m)^\s*Technical Skills\s*\\?\s*$', '', skills_block, flags=re.I)

    # 2. Fix \textbf{Label: rest of content} → \textbf{Label:} rest of content
    #    Matches \textbf{ ... : ... } where the colon is inside the braces
    def fix_textbf(m):
        inner = m.group(1)
        # Find the first colon — everything up to and including it stays bold
        colon_pos = inner.find(':')
        if colon_pos == -1:
            return m.group(0)  # no colon, leave unchanged
        label = inner[:colon_pos + 1]   # e.g. "Testing & QA:"
        rest  = inner[colon_pos + 1:]   # e.g. " Selenium, Playwright..."
        if rest.strip():
            return r'\textbf{' + label + '}' + rest
        return m.group(0)  # nothing after colon, leave unchanged

    skills_block = re.sub(r'\\textbf\{([^}]+)\}', fix_textbf, skills_block)

    # 3. Escape bare & inside \textbf{} labels — unescaped & causes LaTeX "Misplaced alignment tab" error
    def escape_amp_in_textbf(m):
        inner = m.group(1)
        inner = re.sub(r'(?<!\\)&', r'\\&', inner)
        return r'\textbf{' + inner + '}'

    skills_block = re.sub(r'\\textbf\{([^}]+)\}', escape_amp_in_textbf, skills_block)

    return skills_block

def inject_programming_fallback(skills_block):
    """
    If the skills block has no programming/scripting/languages & tools line,
    insert two fallback lines inside the \\item{} block, before its closing brace.
    """
    programming_keywords = re.compile(
        r'\\textbf\{[^}]*(?:Program|Script|Lang|Coding|Develop|Java|SQL|C\+\+)[^}]*\}',
        re.IGNORECASE
    )
    if programming_keywords.search(skills_block):
        return skills_block  # already has programming skills, do nothing

    fallback_lines = (
        '     \\textbf{Programming \\& Scripting:} Java, SQL querying, test automation frameworks \\\\\n'
        '     \\textbf{Database:} Oracle PL/SQL, MongoDB \\\\\n'
    )

    # Find the closing } of \item{...} just before \end{itemize} and insert before it
    # Use a function to avoid re.sub interpreting backslashes in the replacement string
    pattern = r'([ \t]*\})([ \t]*\n[ \t]*\\end\{itemize\})'

    def replacer(m):
        return fallback_lines + m.group(1) + m.group(2)

    new_block, count = re.subn(pattern, replacer, skills_block, count=1)
    if count == 0:
        # Bare block — just append at the end
        new_block = skills_block.rstrip() + '\n' + fallback_lines

    return new_block

def extract_skills_from_reply(reply_text):
    """
    Extract the skills block from Gemini's reply.
    Handles three formats Gemini commonly returns:
      A) Full LaTeX: \\section*{Skills} \\begin{itemize} ... \\end{itemize}
      B) itemize only: \\begin{itemize} ... \\end{itemize}
      C) Bare lines:  \\textbf{Label:} value \\ (no itemize at all)
    """
    content = None

    # --- Strategy A & B: look for LaTeX block with \section* or \begin{itemize} ---
    for pat in [
        r'(?is)\\section\*\s*\{(?:Skills|Technical Skills)\}.*?(?=\\section|\Z)',
        r'(?is)\\begin\{itemize\}.*?\\end\{itemize\}',
    ]:
        m = re.search(pat, reply_text, re.DOTALL)
        if m:
            content = m.group(0).strip()
            break

    # --- Strategy C: bare \textbf{...} lines (Gemini skipped the itemize wrapper) ---
    if not content:
        # Find the section header that precedes the bare lines (e.g. "Revised Skills Section")
        # then grab consecutive \textbf lines until a non-textbf line appears
        bare_match = re.search(
            r'(?im)(?:Revised|Rewritten|Updated|New)?\s*Skills\s*(?:Section|Block)?\s*\n'
            r'((?:\s*\\textbf\{[^}]+\}.*(?:\\\\\s*)?\n?)+)',
            reply_text
        )
        if bare_match:
            content = bare_match.group(1).strip()
        else:
            # Last resort: grab any run of \textbf lines in the reply
            bare_lines = re.findall(r'\\textbf\{[^}]+\}[^\n]+', reply_text)
            if len(bare_lines) >= 2:
                content = '\n'.join(bare_lines)

    if not content:
        print("Could not find any skills block with known patterns.")
        return None

    # --- Normalise backslash line endings (Gemini sometimes uses \ instead of \\) ---
    # Single backslash at end of line → double backslash
    content = re.sub(r'(?<!\\)\\(?!\\|\w|\{)(\s*\n)', r'\\\\\1', content)

    # --- Remove trailing score/analysis text ---
    content = re.sub(r'(Updated|New|Initial)\s*(Match|Score|Analysis).*', '', content, flags=re.I | re.DOTALL)

    # --- Fix common broken nesting / small tags ---
    content = re.sub(r'\\small\s*\{([^}]*)\}', r'\1', content)
    content = re.sub(r'\\item\s*\{([^}]*)\}\s*\{', r'\\item \1 {', content)

    # --- Remove Languages lines ---
    content = remove_languages_from_skills(content)

    # --- Remove 'Technical Skills' sub-header and fix \textbf wrapping full lines ---
    content = clean_skills_block(content)

    # --- If content has no itemize wrapper, build the full block around it ---
    if r'\begin{itemize}' not in content:
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
        # Ensure each line ends with \\
        fixed_lines = []
        for ln in lines:
            if not ln.endswith('\\\\') and not ln.endswith('\\'):
                ln = ln + ' \\\\'
            fixed_lines.append('     ' + ln)
        inner = '\n'.join(fixed_lines)
        content = (
                '\\section*{Skills}\n'
                '\\begin{itemize}[leftmargin=0.15in, label={}]\n'
                '    \\item{\n'
                + inner + '\n'
                          '    }\n'
                          '\\end{itemize}'
        )
    elif not content.strip().startswith('\\section*{Skills}'):
        content = '\\section*{Skills}\n' + content

    # --- Inject commented-out programming fallback if no programming line present ---
    content = inject_programming_fallback(content)

    # --- Final cleanup ---
    content = re.sub(r'\n\s*\n+', '\n', content)
    content = content.strip()

    if len(content) < 80 or r'\end{itemize}' not in content:
        print("Extracted content looks too short or broken → discarding")
        return None

    return content

def send_to_gemini(prompt, output_file="skills.tex"):
    with sync_playwright() as p:
        start_total = time.time()
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        print("Opening Gemini + handling consent...")
        start_goto = time.time()
        page.goto("https://gemini.google.com/", timeout=45000)
        print(f"Goto took {time.time() - start_goto:.2f}s")

        print("Checking for consent screen...")
        start_consent = time.time()
        try:
            reject_btn = page.get_by_role("button", name="Reject all")
            reject_btn.wait_for(state="visible", timeout=8000)
            reject_btn.click()
            print("Clicked 'Reject all'")
            time.sleep(2)
        except:
            print("No consent screen detected (already accepted or skipped)")
        print(f"Consent handling took {time.time() - start_consent:.2f}s")

        start_textbox_wait = time.time()
        try:
            print("abt to fill prompt...")
            page.get_by_role("textbox", name="Enter a prompt for Gemini").wait_for(timeout=30000)
        except:
            print("Main textbox not found by name → will use fallback locator")
        print(f"Textbox wait took {time.time() - start_textbox_wait:.2f}s")

        print("Filling prompt...")
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
                page.locator("rich-textarea").locator("div").nth(1).fill(prompt)
                prompt_filled = True
            except:
                pass
        if not prompt_filled:
            page.locator('[role="textbox"], [contenteditable="true"]').first.fill(prompt)
            print("Used last-resort locator for prompt")
        print("Prompt filled")

        try:
            page.get_by_role("button", name="Send message").click(delay=150)
            print("Message sent")
        except:
            page.locator('button:has(svg)').last.click()
            print("Used fallback send button locator")

        print("Waiting for Gemini reply...")
        reply_text = None
        start = time.time()
        while time.time() - start < 60:
            time.sleep(1.8)
            last_reply = page.locator(
                'div.markdown, '
                'div[role="presentation"] div.markdown, '
                '[data-message-author-role="model"] div.markdown'
            ).last
            if last_reply.is_visible():
                reply_text = last_reply.inner_text().strip()
                if len(reply_text) > 80:
                    break
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
            skills = extract_skills_from_reply(reply_text)
            if skills:
                skills_escaped = skills.replace('\\', '\\\\')
                with open("sample_cv.tex", "r", encoding="utf-8") as f:
                    cv_content = f.read()

                # FIX: Replace ALL occurrences of \section*{Skills}...next-section with a single new block.
                # This handles the case where the CV already has a duplicate skills section.
                skills_section_pattern = r'(?:\\section\*\s*\{Skills\}.*?)+(?=\\section|\Z)'
                new_cv = re.sub(
                    skills_section_pattern,
                    skills_escaped + '\n',
                    cv_content,
                    count=1,           # Replace only the first match (the whole run)
                    flags=re.DOTALL | re.MULTILINE
                )

                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(new_cv)
                print(f"\n✅ Saved updated CV with new Skills to: {output_file}")
            else:
                with open("full_reply.txt", "w", encoding="utf-8") as f:
                    f.write(reply_text)
                print("Skills block not found — full reply saved to full_reply.txt")
        else:
            print("Could not reliably capture the reply after 60s.")
            print("→ Please copy it manually from the browser.")

        browser.close()
        print(f"Total send_to_gemini took {time.time() - start_total:.2f}s")


if __name__ == "__main__":
    fetch_and_save_jobs()
    jobs = get_all_jobs()
    print(f"Found {len(jobs)} jobs. Processing all...")
    for i, job in enumerate(jobs):
        job_num = i + 1
        title = job.get('Title', 'Untitled')
        company = extract_company(title)
        prompt = build_prompt(job, job_num)
        output_file = f"{OUTPUT_FILE_BASE}_{job_num}_{company}.tex"
        print(f"\nProcessing job #{job_num}: {title} (Company: {company})")
        send_to_gemini(prompt, output_file=output_file)
        time.sleep(5)