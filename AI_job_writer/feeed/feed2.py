# imports
import os
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from playwright.sync_api import sync_playwright
import requests
import csv
import io
import time
import re
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Your resume text
def load_resume_txt(path="MyCVsample.txt"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Resume file not found: {path}")
        exit(1)

def load_resume(path="sample_cv.tex"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract only the Skills section
        match = re.search(
            r'\\section\*\{Skills\}.*?(?=\\section|\Z)',
            content, re.DOTALL
        )
        if match:
            skills_raw = match.group(0)
            # Strip LaTeX commands to plain text
            skills_raw = re.sub(r'\\textbf\{([^}]+)\}', r'\1', skills_raw)
            skills_raw = re.sub(r'\\begin\{[^}]+\}|\\end\{[^}]+\}', '', skills_raw)
            skills_raw = re.sub(r'\\item', '-', skills_raw)
            skills_raw = re.sub(r'\\[a-zA-Z]+\*?\{[^}]*\}', '', skills_raw)
            skills_raw = re.sub(r'\\[a-zA-Z]+', '', skills_raw)
            skills_raw = re.sub(r'[{}]', '', skills_raw)
            skills_raw = re.sub(r'\n\s*\n+', '\n', skills_raw).strip()
            print(f"📋 Loaded skills section:\n{skills_raw}\n")
            return skills_raw
        else:
            print("⚠️ Skills section not found in tex file — loading full text")
            return content
    except FileNotFoundError:
        print(f"❌ Resume file not found: {path}")
        exit(1)

RESUME = load_resume()

#RSS_CSV_URL = #"https://rss.app/feeds/Jj5cdbaAJPYnM24X.csv" # StepStone QA
RSS_FEEDS = [
    ("https://rss.app/feeds/1cIR1ioKqvbavRwA.csv", "LinkedIn Playwright/Selenium"),
    ("https://rss.app/feeds/70fRpEBI0ubf6WA2.csv", "LinkedIn Selenium"),
    ("https://rss.app/feeds/Jj5cdbaAJPYnM24X.csv", "StepStone QA")
]
LOCAL_CSV = "jobs_March.csv"
OUTPUT_FILE_BASE = "Vineet_CV"  # Base name for output files, e.g., skills_job_Company_1.tex

def fetch_and_save_jobs():
    """Fetch all RSS feeds, deduplicate globally (including existing CSV), append new jobs."""
    # Load already-seen links from existing CSV
    seen_links = set()
    existing_rows = []
    existing_fieldnames = None

    if os.path.exists(LOCAL_CSV):
        with open(LOCAL_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_fieldnames = reader.fieldnames or []
            for row in reader:
                existing_rows.append(row)
                link = row.get("Link", "").strip()
                if link:
                    seen_links.add(link)
        print(f"Loaded {len(existing_rows)} existing jobs from {LOCAL_CSV}")

    new_rows   = []
    fieldnames = list(existing_fieldnames) if existing_fieldnames else None

    for url, label in RSS_FEEDS:
        print(f"Fetching feed: {label} ...")
        try:
            r = requests.get(url, timeout=20)
            if r.status_code != 200:
                print(f"  ⚠️  Failed (HTTP {r.status_code}) — skipping.")
                continue
        except Exception as e:
            print(f"  ⚠️  Error: {e} — skipping.")
            continue

        reader = csv.DictReader(io.StringIO(r.text))

        if fieldnames is None:
            fieldnames = ["Date", "Title", "Link", "Description", "Source"]

        added = 0
        for row in reader:
            link = row.get("Link", "").strip()
            if link and link in seen_links:
                continue
            if link:
                seen_links.add(link)

            # ── Task 3: strip time from date, keep only clean columns ──
            raw_date = row.get("Date") or row.get("Published") or row.get("pubDate") or ""
            date_only = ""
            if raw_date.strip():
                try:
                    date_only = parsedate_to_datetime(raw_date.strip()).strftime("%Y-%m-%d")
                except Exception:
                    date_only = raw_date.strip().split(" ")[0]

            raw_desc = row.get("Description") or row.get("Summary") or ""
            plain_desc = re.sub(r"<[^>]+>", " ", raw_desc)        # strip HTML tags
            plain_desc = re.sub(r"\s+", " ", plain_desc).strip()   # collapse whitespace

            clean_row = {
                "Date":        date_only,
                "Title":       row.get("Title", "").strip(),
                "Link":        link,
                "Description": plain_desc,
                "Source":      label,
            }
            new_rows.append(clean_row)
            added += 1

        print(f"  ✅ {label}: +{added} new (seen total: {len(seen_links)})")

    if not new_rows:
        print("No new jobs found. CSV unchanged.")
        return

    # Write header + all rows (existing + new) so file is always self-consistent
    all_rows = existing_rows + new_rows
    with open(LOCAL_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date","Title","Link","Description","Source","Generated"],
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n✅ Appended {len(new_rows)} new jobs → {LOCAL_CSV} now has {len(all_rows)} total")

def fetch_and_save_jobs_old():
    r = requests.get(RSS_FEEDS)
    if r.status_code != 200:
        print("Failed to download CSV.")
        exit(1)
    with open(LOCAL_CSV, "w", encoding="utf-8") as f:
        f.write(r.text)
    print("Saved jobs.csv locally.")


GERMAN_REQUIRED_PATTERNS = re.compile(
    r'(?:C1|C2|flie[sß]end|verhandlungssicher|muttersprachlich|native|sehr\s+gute[sn]?)'
    r'(?:[^.]*?(?:deutsch|german))|'
    r'(?:deutsch|german)(?:[^.]*?(?:C1|C2|flie[sß]end|verhandlungssicher|muttersprachlich|native|sehr\s+gute[sn]?))',
    re.IGNORECASE
)

def filter_jobs(jobs):
    """Filter out jobs requiring C1+ German and jobs older than 24 hours."""
    cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    print(f"  🕐 Cutoff: {cutoff_24h.strftime('%Y-%m-%d %H:%M')} UTC")
    filtered = []
    for job in jobs:
        # 24h filter
        date_str = job.get("Date", "").strip()
        if date_str:
            try:
                pub_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if pub_date < cutoff_24h:
                    print(f"  ⏭ Skipping old ({date_str[:10]}): {job.get('Title','')[:60]}")
                    continue
            except Exception:
                pass
        # German C1+ filter
        desc = job.get("Description", "") + " " + job.get("Title", "")
        if GERMAN_REQUIRED_PATTERNS.search(desc):
            print(f"  🇩🇪 Skipping (German C1+ required): {job.get('Title','')[:60]}")
            continue
        filtered.append(job)
    print(f"→ {len(filtered)} jobs after filters ({len(jobs) - len(filtered)} skipped)")
    return filtered


def get_all_jobs():
    filtered = []
    skipped  = 0
    with open(LOCAL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Generated", "").strip():
                skipped += 1
                continue
            filtered.append(row)
    print(f"→ {len(filtered)} unprocessed jobs, {skipped} already generated.")
    return filtered

def mark_job_generated(title, link, output_file):
    rows = []
    with open(LOCAL_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("Link", "") == link:
                row["Generated"] = output_file
            rows.append(row)
    with open(LOCAL_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def get_all_jobs_old():
    cutoff   = datetime.now(timezone.utc) - timedelta(days=7)
    filtered = []
    skipped  = 0
    with open(LOCAL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            date_str = row.get("Date", "").strip()
            if date_str:
                try:
                    # Date is now stored as YYYY-MM-DD (no timezone) — compare as date
                    pub_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if pub_date < cutoff:
                        print(f"  ⏭ Skipping old ({date_str}): {row.get('Title','')[:60]}")
                        skipped += 1
                        continue
                except Exception:
                    pass
            filtered.append(row)
    print(f"→ {len(filtered)} jobs within 7 days, {skipped} skipped.")
    return filtered

def get_all_jobs_old():
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

import yaml

def load_prompts(path="prompts.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

PROMPTS = load_prompts()

def build_prompt(job, job_num):
    template = PROMPTS["prompts"]["build_cv_skills"]
    return (
        template
        .replace("$resume", f"My current skills:\n{RESUME}")
        .replace("$title", job.get("Title", "No title"))
        .replace("$desc",  job.get("Description", "No description"))
    )

def build_prompt_old(job, job_num):
    title = job.get('Title', 'No title')
    desc = job.get('Description', 'No description')
    return (
        "/no_think\n"
        f"Here is my resume:\n{RESUME}\n\n"
        f"Here is a job ad:\n"
        f"Title: {title}\n"
        f"Description: {desc}\n\n"
        "Respond with EXACTLY this structure, nothing else:\n\n"
        "1. Match score: X%\n\n"
        "2. Rewritten Skills section (LaTeX):\n"
        "\\begin{itemize}\n"
        "\\item \\textbf{Label:} skill1, skill2, skill3\n"
        "\\end{itemize}\n\n"
        "3. New match score: X%\n\n"
        "STRICT RULES for the skills block:\n"
        "- Use ONLY skills from MY RESUME above — do NOT copy from the job ad\n"
        "- Reorder and emphasise skills most relevant to this job\n"
        "- Each \\item must be: \\textbf{Category:} skill1, skill2, skill3\n"
        "- Do NOT use \\begin{verbatim}, \\documentclass, or any LaTeX preamble\n"
        "- Do NOT add a Languages entry\n"
        "- Do NOT include percentages inside the skills block\n"
        "- 5-8 items maximum\n"
    )
    
def build_prompt_old2(job, job_num):
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
    programming_keywords = re.compile(
        r'\\textbf\{[^}]*(?:Program|Script|Lang|Coding|Develop|Java|SQL|C\+\+)[^}]*\}',
        re.IGNORECASE
    )
    if programming_keywords.search(skills_block):
        return skills_block  # already has programming skills, do nothing

    fallback_lines = (
        '\\item \\textbf{Programming \\& Scripting:} Java, SQL querying, test automation frameworks\n'
        '\\item \\textbf{Database:} Oracle PL/SQL, MongoDB\n'
    )

    # Insert before \end{itemize}
    new_block = re.sub(
        r'(\\end\{itemize\})',
        fallback_lines + r'\1',
        skills_block,
        count=1
    )

    if new_block == skills_block:
        # No \end{itemize} found — just append
        new_block = skills_block.rstrip() + '\n' + fallback_lines

    return new_block

# 7. Remove duplicate skills appearing in multiple \item lines
def dedup_skills(content):
    seen = set()
    result_lines = []
    for line in content.splitlines():
        if r'\item' in line and r'\textbf' in line:
            colon_pos = line.find(':}')
            if colon_pos != -1:
                prefix = line[:colon_pos + 2]
                skills_part = line[colon_pos + 2:]
            else:
                m = re.search(r'\\textbf\{[^}]+\}\s*', line)
                if m:
                    prefix = line[:m.end()]
                    skills_part = line[m.end():]
                else:
                    result_lines.append(line)
                    continue
            skills = [s.strip() for s in skills_part.split(',') if s.strip()]
            deduped = [s for s in skills if s.lower() not in seen]
            seen.update(s.lower() for s in deduped)
            line = prefix + ' ' + ', '.join(deduped)
        result_lines.append(line)
    return '\n'.join(result_lines)

def extract_skills_from_reply(reply_text):
    """
    Extract the skills block from LLM reply.
    Handles formats from Mistral, Gemini, Grok:
      A) Full LaTeX: \\section*{Skills} \\begin{itemize} ... \\end{itemize}
      B) itemize only: \\begin{itemize} ... \\end{itemize}
      C) verbatim-wrapped: \\begin{verbatim} ... \\end{verbatim}
      D) Bare lines: \\textbf{Label:} value \\\\ (no itemize at all)
    """

    # ── Pre-processing ──────────────────────────────────────────────────────────

    # 1. Unwrap \begin{verbatim}...\end{verbatim} — Mistral wraps output in this
    reply_text = re.sub(
        r'\\begin\{verbatim\}(.*?)\\end\{verbatim\}',
        lambda m: m.group(1),
        reply_text, flags=re.DOTALL
    )

    # 2. Strip any accidental \documentclass preamble (Mistral hallucination)
    reply_text = re.sub(r'(?s)\\documentclass.*?\\begin\{document\}', '', reply_text)
    reply_text = re.sub(r'\\end\{document\}', '', reply_text)

    # 3. Strip markdown code fences (```latex ... ``` or ``` ... ```)
    reply_text = re.sub(r'```(?:latex|tex)?\s*(.*?)\s*```', lambda m: m.group(1), reply_text, flags=re.DOTALL)

    # 4. Strip <think>...</think> blocks (qwen3 thinking mode)  ← ADD THIS
    reply_text = re.sub(r'<think>.*?</think>', '', reply_text, flags=re.DOTALL)
    
    # 5. Fix hallucinated commands like \Checklist, \Note, \Highlight etc.
    reply_text = re.sub(r'\\(?!item|textbf|begin|end|section|subsection|hfill|textit|href)[A-Za-z]+:', 
                    r'\\item \\textbf{Tools \& Stack:}', reply_text)
                    
    # 6. Remove inline model commentary like (addendum: ...) or (note: ...) or (consider: ...)
    reply_text = re.sub(r'\((?:addendum|note|consider|tip|suggestion)[^)]*\)', '', reply_text, flags=re.I)
    content = None
    
    # ── Strategy A: \section*{Skills} block ─────────────────────────────────────
    m = re.search(
        r'(?is)\\section\*\s*\{(?:Skills|Technical Skills)\}.*?(?=\\section|\Z)',
        reply_text, re.DOTALL
    )
    if m:
        content = m.group(0).strip()

    # ── Strategy B: \begin{itemize} ... \end{itemize} ───────────────────────────
    if not content:
        m = re.search(r'(?is)\\begin\{itemize\}.*?\\end\{itemize\}', reply_text, re.DOTALL)
        if m:
            content = m.group(0).strip()

    # ── Strategy C: itemize was inside verbatim (already unwrapped above),
    #    but model used \item{} style instead of \item ──────────────────────────
    if not content:
        m = re.search(r'(?is)\\begin\{enumerate\}.*?\\end\{enumerate\}', reply_text, re.DOTALL)
        if m:
            # Convert enumerate → itemize
            content = m.group(0).strip()
            content = content.replace(r'\begin{enumerate}', r'\begin{itemize}')
            content = content.replace(r'\end{enumerate}', r'\end{itemize}')

    # ── Strategy D: bare \textbf lines (no itemize wrapper) ─────────────────────
    if not content:
        bare_match = re.search(
            r'(?im)(?:Revised|Rewritten|Updated|New)?\s*Skills\s*(?:Section|Block)?\s*\n'
            r'((?:\s*\\textbf\{[^}]+\}.*(?:\\\\\s*)?\n?)+)',
            reply_text
        )
        if bare_match:
            content = bare_match.group(1).strip()
        else:
            bare_lines = re.findall(r'\\textbf\{[^}]+\}[^\n]+', reply_text)
            if len(bare_lines) >= 2:
                content = '\n'.join(bare_lines)

    if not content:
        print("Could not find any skills block with known patterns.")
        return None

    # ── Normalisation ────────────────────────────────────────────────────────────

    # Single backslash at end of line → double backslash
    content = re.sub(r'(?<!\\)\\(?!\\|\w|\{)(\s*\n)', r'\\\\\1', content)

    # Remove trailing score/analysis text that leaked into the block
    content = re.sub(r'(Updated|New|Initial)\s*(Match|Score|Analysis).*', '', content, flags=re.I | re.DOTALL)

    # Fix \small{} and broken \item{} nesting
    content = re.sub(r'\\small\s*\{([^}]*)\}', r'\1', content)
    content = re.sub(r'\\item\s*\{([^}]*)\}\s*\{', r'\\item \1 {', content)

    # Remove Languages lines
    content = remove_languages_from_skills(content)

    # Remove 'Technical Skills' sub-header and fix \textbf wrapping full lines
    content = clean_skills_block(content)

    # ── Wrap bare content in itemize if needed ───────────────────────────────────
    if r'\begin{itemize}' not in content:
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
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

    # ── Inject programming fallback if missing ───────────────────────────────────
    content = inject_programming_fallback(content)

    # ── Dedup skills — MUST be after content is extracted ───────────────────────
    content = dedup_skills(content)

    # ── Final cleanup ────────────────────────────────────────────────────────────
    content = re.sub(r'\n\s*\n+', '\n', content)
    content = content.strip()

    if len(content) < 80 or r'\end{itemize}' not in content:
        print("Extracted content looks too short or broken → discarding")
        return None

    return content

def extract_skills_from_reply_old(reply_text):
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


import google.generativeai as genai
genai.configure(api_key="key")
def send_to_gemini_api(prompt, output_file="skills.tex"):
    model = genai.GenerativeModel("gemini-2.0-flash")
    #model = genai.GenerativeModel("gemini-2.5-flash")

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            reply_text = response.text
            print("\n=== GEMINI REPLY ===\n", reply_text[:300])
            skills = extract_skills_from_reply(reply_text)
            if skills:
                skills_esc = skills.replace("\\", "\\\\")
                with open("sample_cv.tex", "r", encoding="utf-8") as f:
                    cv = f.read()
                new_cv = re.sub(
                    r"(?:\\section\*\s*\{Skills\}.*?)+(?=\\section|\Z)",
                    skills_esc + "\n",
                    cv, count=1, flags=re.DOTALL | re.MULTILINE
                )
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(new_cv)
                print(f"✅ Saved: {output_file}")
            else:
                with open("full_reply.txt", "w", encoding="utf-8") as f:
                    f.write(reply_text)
                print("Skills block not found — saved to full_reply.txt")
            return  # success

        except Exception as e:
            err = str(e)
            if "429" in err:
                # Extract retry delay from error message
                delay_match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', err)
                wait = int(delay_match.group(1)) + 5 if delay_match else 60
                print(f"⏳ Rate limited — waiting {wait}s (attempt {attempt+1}/3)...")
                time.sleep(wait)
            else:
                print(f"❌ Gemini API error: {e}")
                return

def extract_company(title):
    # Try "sucht" or "hiring" pattern first
    match = re.match(r"^(.*?)(?: sucht|hiring) ", title, re.IGNORECASE)
    if match:
        company = match.group(1).strip()
    else:
        # Try "Job at COMPANY in" pattern (StepStone format)
        match = re.match(r".*?\bat\s+(.+?)\s+in\b", title, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
        else:
            return "unknown"
    company = re.sub(r'[^\w\-]', '_', company)
    company = re.sub(r'_+', '_', company).strip('_')
    return company


def _fill_and_capture_gemini(page, prompt, output_file):
    """Shared logic for filling prompt and capturing Gemini reply."""

    # Handle consent screen
    try:
        reject_btn = page.get_by_role("button", name="Reject all")
        reject_btn.wait_for(state="visible", timeout=8000)
        reject_btn.click()
        print("Clicked 'Reject all'")
        time.sleep(2)
    except:
        print("No consent screen detected")

    # Wait for textbox
    try:
        page.get_by_role("textbox", name="Enter a prompt for Gemini").wait_for(timeout=30000)
    except:
        print("Main textbox not found by name → will use fallback locator")

    # Fill prompt
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
        try:
            page.locator('[role="textbox"], [contenteditable="true"]').first.fill(prompt)
            prompt_filled = True
            print("Used last-resort locator for prompt")
        except:
            print("❌ Could not fill prompt — all locators failed")
            return
    print("Prompt filled")

    # Send
    try:
        page.get_by_role("button", name="Send message").click(delay=150)
        print("Message sent")
    except:
        try:
            page.locator('button:has(svg)').last.click()
            print("Used fallback send button")
        except:
            page.keyboard.press("Enter")
            print("Used keyboard Enter to send")

    # Wait for reply
    print("⏳ Waiting for Gemini response...")
    reply_text = None
    start = time.time()
    while time.time() - start < 90:
        time.sleep(1.8)
        try:
            last_reply = page.locator(
                'div.markdown, '
                'div[role="presentation"] div.markdown, '
                '[data-message-author-role="model"] div.markdown'
            ).last
            if last_reply.is_visible():
                text = last_reply.inner_text().strip()
                if len(text) > 80:
                    reply_text = text
                    break
        except:
            pass
        try:
            model_responses = page.locator('[id^="model-response-message-contentr_"]')
            if model_responses.count() > 0:
                text = model_responses.last.inner_text().strip()
                if len(text) > 80:
                    reply_text = text
                    break
        except:
            pass

    if not reply_text:
        print("❌ Could not capture reply after 90s")
        return

    print("\n=== GEMINI REPLY ===\n", reply_text[:300])

    # Extract and save skills
    skills = extract_skills_from_reply(reply_text)
    if skills:
        skills_esc = skills.replace('\\', '\\\\')
        with open("sample_cv.tex", "r", encoding="utf-8") as f:
            cv = f.read()
        new_cv = re.sub(
            r'(?:\\section\*\s*\{Skills\}.*?)+(?=\\section|\Z)',
            skills_esc + '\n',
            cv, count=1, flags=re.DOTALL | re.MULTILINE
        )
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(new_cv)
        print(f"✅ Saved: {output_file}")
    else:
        with open("full_reply.txt", "w", encoding="utf-8") as f:
            f.write(reply_text)
        print("Skills block not found — saved to full_reply.txt")


def send_to_gemini(prompt, output_file="skills.tex"):
    """Launch new browser and use Gemini UI."""
    with sync_playwright() as p:
        start_total = time.time()
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        print("Opening Gemini...")
        page.goto("https://gemini.google.com/", timeout=45000)
        _fill_and_capture_gemini(page, prompt, output_file)
        browser.close()
        print(f"Total send_to_gemini took {time.time() - start_total:.2f}s")


def send_to_gemini_cdp(prompt, output_file="skills.tex"):
    """Connect to already-open Chrome via CDP and use Gemini UI.

    Launch Chrome first with:
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        --remote-debugging-port=9222 --user-data-dir="C:\\chrome-debug"
    Then log into gemini.google.com manually before running script.
    """
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]

            # Find existing Gemini tab or open new one
            gemini_page = None
            for page in context.pages:
                if "gemini.google.com" in page.url:
                    gemini_page = page
                    break
            if not gemini_page:
                gemini_page = context.new_page()
                gemini_page.goto("https://gemini.google.com/", timeout=30000)
                time.sleep(3)

            gemini_page.bring_to_front()
            time.sleep(2)
            gemini_page.wait_for_load_state("domcontentloaded")

            # Start new chat to avoid context bleed from previous job
            try:
                new_chat = gemini_page.get_by_role("link", name="New chat")
                if new_chat.is_visible():
                    new_chat.click()
                    time.sleep(2)
            except:
                pass

            _fill_and_capture_gemini(gemini_page, prompt, output_file)

        except Exception as e:
            print(f"❌ CDP Gemini error: {e}")

def send_to_local_llm(prompt, output_file="skills.tex", model="qwen3:8b"):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_gpu": 18,
            "num_predict": 800,
             # "thinking": False,
        }
    }
    for attempt in range(3):
        try:
            response = requests.post(url, json=data, timeout=300)
            #print(f"🔍 Status: {response.status_code}")
            #print(f"🔍 Raw: {response.text[:1000]}")
            if response.status_code != 200:
                print(f"❌ Ollama error: HTTP {response.status_code} - {response.text}")
                time.sleep(5)
                continue

            reply_data = response.json()  # call ONCE
            reply_text = reply_data.get("response", "").strip()

            if not reply_text:
                print(f"⚠️ Empty response (attempt {attempt+1}/3), retrying in 10s...")
                time.sleep(10)
                continue

            print("\n=== OLLAMA REPLY ===\n", reply_text[:300])
            skills = extract_skills_from_reply(reply_text)
            if skills:
                skills_esc = skills.replace("\\", "\\\\")
                with open("sample_cv.tex", "r", encoding="utf-8") as f:
                    cv = f.read()
                new_cv = re.sub(
                    r"(?:\\section\*\s*\{Skills\}.*?)+(?=\\section|\Z)",
                    skills_esc + "\n",
                    cv, count=1, flags=re.DOTALL | re.MULTILINE
                )
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(new_cv)
                print(f"✅ Saved: {output_file}")
            else:
                with open("full_reply.txt", "w", encoding="utf-8") as f:
                    f.write(reply_text)
                print("Skills block not found — saved to full_reply.txt")
            return  # success — exit retry loop

        except Exception as e:
            print(f"❌ Local LLM error (attempt {attempt+1}/3): {e}")
            time.sleep(10)

if __name__ == "__main__":
    fetch_and_save_jobs()
    jobs = get_all_jobs()
    jobs = filter_jobs(jobs)
    print(f"Found {len(jobs)} jobs after filtering.")

    today_ddmm = datetime.now().strftime("%d%m")

    # ── Full loop ────────────────────────────────────────────────────────────
    for i, job in enumerate(jobs):
        num     = i + 1
        title   = job.get("Title", "Untitled")
        company = extract_company(title)
        prompt  = build_prompt(job, num)
        out     = f"{OUTPUT_FILE_BASE}_{today_ddmm}_{num:02d}_{company}.tex"
        print(f"\nJob #{num}: {title}  [source: {job.get('Source','?')}  company: {company}]")
        print(f"Output → {out}")
        #"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
        send_to_gemini_cdp(prompt, output_file=out)

        #send_to_gemini_api(prompt, output_file=out)
        # send_to_local_llm(prompt, output_file=out)
        # send_to_gemini(prompt, output_file=out)
        if os.path.exists(out) and os.path.getsize(out) > 500:
            mark_job_generated(title, job.get("Link", ""), out)
            print(f"✅ Marked as generated in CSV")
        else:
            print(f"⚠️ File missing or too small — NOT marked as generated")
        if i < len(jobs) - 1:
            print("  ⏳ Waiting 10s between jobs (free tier rate limit)...")
            time.sleep(15)

    # ── Manual single-job test ───────────────────────────────────────────────
    # job     = jobs[0]
    # num     = 1
    # title   = job.get("Title", "Untitled")
    # company = extract_company(title)
    # prompt  = build_prompt(job, num)
    # out     = f"{OUTPUT_FILE_BASE}_{today_ddmm}_01_TEST_{company}.tex"
    # print(f"\nJob #1: {title}")
    # print(f"Output → {out}")
    # print(f"📏 Prompt length: {len(prompt)}")
    # print(f"📝 Prompt preview:\n{prompt[:500]}")
    # send_to_gemini_api(prompt, output_file=out)
    # send_to_local_llm(prompt, output_file=out)
    # send_to_gemini(prompt, output_file=out)
    # if os.path.exists(out) and os.path.getsize(out) > 500:
    #     mark_job_generated(title, job.get("Link", ""), out)
    #     print(f"✅ Marked as generated in CSV")
    # else:
    #     print(f"⚠️ File missing or too small — NOT marked as generated")
