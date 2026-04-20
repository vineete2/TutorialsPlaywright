import csv
import io
import sys
import argparse
import os
import re
import json
import urllib.request
import urllib.error
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — Edit this section to match YOUR profile
# ─────────────────────────────────────────────────────────────────────────────

STRONG_SKILLS = [
    "selenium", "playwright", "cypress", "python", "java",
    "ci/cd", "jenkins", "gitlab", "cucumber", "bdd",
    "agile", "scrum", "postman", "api", "regression", "exploratory",
    "docker", "github actions", "test automation", "quality assurance",
    "qa", "robot framework", "pytest", "e2e", "end-to-end", "appium",
    "tosca", "tricentis", "xray", "zephyr", "testrail",
]

SECONDARY_SKILLS = [
    "testng", "jest", "maven", "javascript", "typescript",
    "spring boot", "c#", "azure devops", "linux", "git", "devops",
    "rest", "graphql", "kanban", "functional", "test case",
    "test plan", "defect", "jira", "confluence", "sql",
]

HARD_DISQUALIFIERS = [
    "mechanical engineer", "subsea", "oil and gas", "plumbing",
    "electrical qc", "qc engineer", "manufacturing qa", "manufacturing qc",
    "commissioning engineer ertms", "railway signal", "jernbanesignal",
    "hardware qa", "embedded test", "hw qa", "pcb", "iec 62304",
    "e&p engineer", "m&p engineer",
    "intern", "internship", "vikariat",
    "head of engineering productivity",
    "2d document processing",
    "mainframe", "cobol", "pl/i", "alternator", "mechatronik",
    "hochfrequenztechnik", "fluidtechnik", "gebäudeautomation",
    "netzwerk / security", "netzwerk/security",
]

# These disqualifiers must match as whole words only (not substrings).
# "intern" would otherwise match "internal", "internationale", "internen" etc.
# in German/French job descriptions, causing false disqualifications.
WORD_BOUNDARY_DISQUALIFIERS = {"intern", "internship", "vikariat"}

MULTILANG_SYNONYMS = {
    "test automation":    ["testautomatisierung", "test-automatisierung", "testautomatisierer"],
    "quality assurance":  ["qualitätssicherung", "qualitätskontrolle", "qualitaetssicherung",
                           "assurance qualité", "assurance-qualité", "contrôle qualité"],
    "software testing":   ["softwaretest", "softwaretesting", "softwareprüfung", "softwaretester",
                           "test logiciel", "tests logiciels", "testeur", "testeuse",
                           "recette", "tests fonctionnels", "test fonctionnel",
                           "programvaretesting", "mjukvarutestning", "ohjelmistotestaus", "testingeniør"],
    "regression":         ["regressionstests", "regressionstest",
                           "tests de régression", "régression", "non-régression", "non régression",
                           "regresjonstest"],
    "test automation":    ["automatisation des tests", "automatisation de test"],
    "agile":              ["agiles", "agilität", "agile methoden", "méthodologie agile", "méthode agile",
                           "smidig", "agil utvikling"],
    "scrum":              ["scrum-master", "scrum-team"],
    "defect":             ["fehler", "fehlerbericht", "défaut", "anomalie", "bogue", "feil"],
    "test case":          ["testfall", "testfälle", "cas de test", "cas d'essai", "testtilfelle"],
    "test plan":          ["testplan", "testplanung"],
    "qa":                 ["qualitätsprüfung", "assurance qualité", "qualité logicielle"],
}

# ─────────────────────────────────────────────────────────────────────────────
# SCORING THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────────

MATCH_THRESHOLD              = 55
BORDERLINE_THRESHOLD         = 35
MATCH_THRESHOLD_NO_DESC      = 20   # lower bar when job has no description
BORDERLINE_THRESHOLD_NO_DESC = 10
MAX_RAW_POINTS               = 100

# ─────────────────────────────────────────────────────────────────────────────
# COUNTRY DETECTION
# ─────────────────────────────────────────────────────────────────────────────

COUNTRY_TAG_MAP = {
    "germany": "DE", "france": "FR", "norway": "NO",
    "sweden": "SE",  "finland": "FI", "denmark": "DK",
    "austria": "AT", "swiss": "CH",  "netherlands": "NL", "belgium": "BE",
}

FLAG_MAP = {
    "DE": "🇩🇪", "FR": "🇫🇷", "NO": "🇳🇴",
    "SE": "🇸🇪", "FI": "🇫🇮", "DK": "🇩🇰",
    "AT": "🇦🇹", "CH": "🇨🇭", "NL": "🇳🇱", "BE": "🇧🇪",
}


def detect_country(country_field):
    if not isinstance(country_field, str):
        return "XX"
    lower = country_field.lower()
    for tag, code in COUNTRY_TAG_MAP.items():
        if tag in lower:
            return code
    return "XX"


# ─────────────────────────────────────────────────────────────────────────────
# SKILLS SECTION LANGUAGE TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────

SKILLS_TEMPLATE_EN = {
    "section_title": "Skills",
    "test_automation": "Test Automation",
    "programming":     "Programming \\& Scripting",
    "cicd":            "CI/CD \\& DevOps",
    "api":             "API Testing",
    "qa_method":       "QA Methodology",
    "tools":           "Tools",
}

SKILLS_TEMPLATE_DE = {
    "section_title": "Kenntnisse",
    "test_automation": "Testautomatisierung",
    "programming":     "Programmierung \\& Skripting",
    "cicd":            "CI/CD \\& DevOps",
    "api":             "API-Testing",
    "qa_method":       "QS-Methodik",
    "tools":           "Werkzeuge",
}

# ─────────────────────────────────────────────────────────────────────────────
# SKILLS CATALOGUE
# ─────────────────────────────────────────────────────────────────────────────

CATALOGUE = {
    "selenium":          ("test_automation", "Selenium WebDriver"),
    "playwright":        ("test_automation", "Playwright"),
    "cypress":           ("test_automation", "Cypress"),
    "testng":            ("test_automation", "TestNG"),
    "cucumber":          ("test_automation", "Cucumber / BDD"),
    "bdd":               ("test_automation", "Cucumber / BDD"),
    "robot framework":   ("test_automation", "Robot Framework"),
    "pytest":            ("test_automation", "pytest"),
    "appium":            ("test_automation", "Appium"),
    "jest":              ("test_automation", "Jest"),
    "tosca":             ("test_automation", "Tricentis TOSCA"),
    "tricentis":         ("test_automation", "Tricentis TOSCA"),
    "xray":              ("test_automation", "Xray"),
    "zephyr":            ("test_automation", "Zephyr"),
    "testrail":          ("test_automation", "TestRail"),
    "test automation":   ("test_automation", "Test Automation"),
    "python":            ("programming",     "Python"),
    "java":              ("programming",     "Java"),
    "javascript":        ("programming",     "JavaScript / TypeScript"),
    "typescript":        ("programming",     "JavaScript / TypeScript"),
    "sql":               ("programming",     "SQL"),
    "maven":             ("programming",     "Maven"),
    "spring boot":       ("programming",     "Spring Boot"),
    "c#":                ("programming",     "C#"),
    "ci/cd":             ("cicd",            "CI/CD"),
    "jenkins":           ("cicd",            "Jenkins"),
    "gitlab":            ("cicd",            "GitLab CI/CD"),
    "github actions":    ("cicd",            "GitHub Actions"),
    "docker":            ("cicd",            "Docker"),
    "git":               ("cicd",            "Git"),
    "linux":             ("cicd",            "Linux"),
    "azure devops":      ("cicd",            "Azure DevOps"),
    "devops":            ("cicd",            "DevOps"),
    "postman":           ("api",             "Postman"),
    "api":               ("api",             "REST API testing"),
    "rest":              ("api",             "REST API testing"),
    "graphql":           ("api",             "GraphQL"),
    "agile":             ("qa_method",       "Agile / Scrum"),
    "scrum":             ("qa_method",       "Agile / Scrum"),
    "regression":        ("qa_method",       "Regression Testing"),
    "exploratory":       ("qa_method",       "Exploratory Testing"),
    "e2e":               ("qa_method",       "E2E Testing"),
    "end-to-end":        ("qa_method",       "E2E Testing"),
    "functional":        ("qa_method",       "Functional Testing"),
    "test case":         ("qa_method",       "Test Case Design"),
    "test plan":         ("qa_method",       "Test Planning"),
    "defect":            ("qa_method",       "Defect Management"),
    "kanban":            ("qa_method",       "Kanban"),
    "quality assurance": ("qa_method",       "Quality Assurance"),
    "qa":                ("qa_method",       "Quality Assurance"),
    "jira":              ("tools",           "Jira"),
    "confluence":        ("tools",           "Confluence"),
}

DE_SKILL_NAMES = {
    "CI/CD":              "CI/CD-Pipelines",
    "Regression Testing": "Regressionstests",
    "Exploratory Testing":"Explorative Tests",
    "E2E Testing":        "End-to-End-Tests",
    "Functional Testing": "Funktionale Tests",
    "Test Case Design":   "Testfalldesign",
    "Test Planning":      "Testplanung",
    "Defect Management":  "Defect Management",
    "Agile / Scrum":      "Agile / Scrum",
    "Quality Assurance":  "Qualitätssicherung",
    "Test Automation":    "Testautomatisierung",
    "REST API testing":   "REST API testing",
}

CATEGORY_ORDER = ["test_automation", "programming", "cicd", "api", "qa_method", "tools"]

ALWAYS_INCLUDE = {
    "test_automation": ["Selenium WebDriver", "Playwright"],
    "programming":     ["Java", "Python", "SQL"],
    "cicd":            ["CI/CD", "Git"],
    "api":             ["Postman", "REST API testing"],
    "qa_method":       ["Agile / Scrum", "Defect Management"],
    "tools":           ["Jira", "Confluence"],
}


# ─────────────────────────────────────────────────────────────────────────────
# CORE SCORING
# ─────────────────────────────────────────────────────────────────────────────

def build_keyword_list():
    strong_expanded    = [(sk, 10) for sk in STRONG_SKILLS]
    secondary_expanded = [(sk, 5)  for sk in SECONDARY_SKILLS]
    for base_term, translations in MULTILANG_SYNONYMS.items():
        pts = 10 if base_term in STRONG_SKILLS else 5
        lst = strong_expanded if base_term in STRONG_SKILLS else secondary_expanded
        for t in translations:
            lst.append((t, pts))
    return strong_expanded, secondary_expanded


def is_hard_disqualified(title, desc):
    """
    Returns True if the job should be disqualified.

    FIX: Keywords in WORD_BOUNDARY_DISQUALIFIERS (e.g. "intern") are matched
    with \\b word boundaries so they don't fire on substrings inside other words
    (e.g. German "internen", "internationale", "DKB-internen").
    """
    combined = (title + " " + (desc or "")).lower()
    for kw in HARD_DISQUALIFIERS:
        if kw in WORD_BOUNDARY_DISQUALIFIERS:
            if re.search(r'\b' + re.escape(kw) + r'\b', combined):
                return True
        else:
            if kw in combined:
                return True
    return False


def score_job(title, desc, strong_keywords, secondary_keywords):
    has_desc = bool(desc and desc.strip())
    combined = (title + " " + (desc or "")).lower()
    raw_pts  = 0
    matched  = []

    if any(k in combined for k in ["qa", "quality assurance", "test", "tester", "testing",
                                   "testeur", "testeuse", "recette"]):
        raw_pts += 15

    for kw, pts in strong_keywords:
        if kw in combined:
            raw_pts += pts
            matched.append(f"{kw}(+{pts})")

    for kw, pts in secondary_keywords:
        if kw in combined:
            raw_pts += pts
            matched.append(f"{kw}(+{pts})")

    if any(k in combined for k in ["english required", "english fluent", "fluency in english",
                                   "must speak english", "english speaking", "english is required"]):
        raw_pts += 5

    if any(k in combined for k in ["10+ years", "8+ years", "head of", "vp of",
                                   "principal engineer", "senior lead"]):
        raw_pts -= 15
    elif any(k in combined for k in ["senior", "5+ years", "5 years", "lead "]):
        raw_pts -= 5

    score = min(max(int((raw_pts / MAX_RAW_POINTS) * 100), 0), 100)
    return score, matched, has_desc


def get_verdict(score, has_desc):
    mt = MATCH_THRESHOLD      if has_desc else MATCH_THRESHOLD_NO_DESC
    bt = BORDERLINE_THRESHOLD if has_desc else BORDERLINE_THRESHOLD_NO_DESC
    if score >= mt:   return "✅ MATCH"
    elif score >= bt: return "🟡 BORDERLINE"
    else:             return "❌ SKIP"


# ─────────────────────────────────────────────────────────────────────────────
# CLAUDE API
# ─────────────────────────────────────────────────────────────────────────────

def call_claude_api(prompt, max_tokens=600):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={"Content-Type": "application/json", "x-api-key": api_key,
                 "anthropic-version": "2023-06-01"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"].strip()
    except Exception as e:
        print(f"  [Claude API error: {e}]", file=sys.stderr)
        return None


def build_skills_section_claude(job_title, job_desc, matched_skills, country_code):
    lang = ("Respond in GERMAN. Use German terminology."
            if country_code == "DE"
            else "Respond in ENGLISH.")
    matched_str = ", ".join(
        re.match(r'(.+?)\(\+\d+\)', s).group(1).strip()
        for s in matched_skills if re.match(r'(.+?)\(\+\d+\)', s)
    ) or "selenium, python, ci/cd, agile, jira"

    prompt = f"""You are a QA engineer writing a skills section for a job application.
Job title: {job_title}
Matched skills: {matched_str}
{lang}
Return ONLY valid JSON with exactly these keys (no markdown):
{{"test_automation":[],"programming":[],"cicd":[],"api":[],"qa_method":[],"tools":[]}}
Always include: Selenium WebDriver, Playwright, Python, Java, CI/CD, Git, Postman, REST API testing, Jira, Confluence, Agile / Scrum.
Add job-specific matched skills. Max 7 items per list."""

    response = call_claude_api(prompt)
    if not response:
        return None
    response = re.sub(r"```(?:json)?", "", response).strip()
    try:
        data = json.loads(response)
        for key in CATEGORY_ORDER:
            if key not in data or not isinstance(data[key], list):
                return None
        return data
    except json.JSONDecodeError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# SKILLS SECTION BUILDER (keyword fallback)
# ─────────────────────────────────────────────────────────────────────────────

def build_skills_section_local(matched_skills, country_code):
    buckets = {cat: list(items) for cat, items in ALWAYS_INCLUDE.items()}
    for entry in matched_skills:
        m = re.match(r'(.+?)\(\+\d+\)', entry)
        if not m:
            continue
        keyword = m.group(1).strip().lower()
        if keyword in CATALOGUE:
            cat, display = CATALOGUE[keyword]
            buckets[cat].append(display)
    for cat in CATEGORY_ORDER:
        seen = []
        for item in buckets[cat]:
            if item not in seen:
                seen.append(item)
        buckets[cat] = seen
    if country_code == "DE":
        for cat in CATEGORY_ORDER:
            buckets[cat] = [DE_SKILL_NAMES.get(s, s) for s in buckets[cat]]
    return buckets


# ─────────────────────────────────────────────────────────────────────────────
# LaTeX HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def escape_tex(s):
    if not isinstance(s, str):
        return ""
    s = s.replace("\\", r"\textbackslash{}")
    for char, rep in [("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                      ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                      ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")]:
        s = s.replace(char, rep)
    return s


def render_skills_block(buckets, template):
    lines = [f"\\section*{{{template['section_title']}}}", "\\begin{itemize}"]
    label_map = {k: v for k, v in template.items() if k != "section_title"}
    for cat in CATEGORY_ORDER:
        items = buckets.get(cat, [])
        if not items:
            continue
        label = label_map.get(cat, cat)
        lines.append(f"\\item \\textbf{{{label}:}} {', '.join(escape_tex(i) for i in items)}")
    lines.append("\\end{itemize}")
    return lines


def format_comment_header(score, country_code, job_title, job_link, has_desc):
    flag    = FLAG_MAP.get(country_code, "")
    note    = " [title-only]" if not has_desc else ""
    return [
        f"% Score: {score}%{note} | {flag} {country_code}",
        "% ──────────────────────────────────────────────────────────────",
        f"% {escape_tex(job_title)}",
        f"% Link: {job_link}",
        "",
    ]


# ─────────────────────────────────────────────────────────────────────────────
# CSV LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_csv(filepath, title_col, desc_col, link_col, country_col=3):
    raw  = open(filepath, encoding="utf-8-sig", errors="replace").read()
    jobs = []
    for i, row in enumerate(csv.reader(io.StringIO(raw))):
        if i == 0 and row[title_col].strip().lower() in ["title", "job title", "jobtitle"]:
            continue
        if len(row) <= max(title_col, desc_col):
            continue
        title   = row[title_col].strip()
        desc    = row[desc_col].strip()
        link    = row[link_col].strip()    if len(row) > link_col    else ""
        country = row[country_col].strip() if len(row) > country_col else ""
        if title:
            jobs.append({"title": title, "desc": desc, "link": link, "country": country})
    return jobs


# ─────────────────────────────────────────────────────────────────────────────
# TEX FILE WRITER
# ─────────────────────────────────────────────────────────────────────────────

def write_tex_file(results, output_path, use_claude):
    suitable = [r for r in results if r["verdict"] in ("✅ MATCH", "🟡 BORDERLINE")]
    suitable.sort(key=lambda x: -x["score"])
    matches = sum(1 for r in suitable if r["verdict"] == "✅ MATCH")
    borders = len(suitable) - matches

    lines = [
        "% ═══════════════════════════════════════════════════════════════════",
        f"% Suitable Jobs Skills Sections  ({matches} MATCH + {borders} BORDERLINE)",
        "% Generated by job_scorer.py",
        "% ═══════════════════════════════════════════════════════════════════",
        "",
    ]

    for r in suitable:
        country_code = detect_country(r.get("country", ""))
        template     = SKILLS_TEMPLATE_DE if country_code == "DE" else SKILLS_TEMPLATE_EN

        buckets = None
        if use_claude:
            print(f"  [Claude] {r['title'][:60]}...", file=sys.stderr)
            buckets = build_skills_section_claude(r["title"], r["desc"], r["matched"], country_code)
            if buckets is None:
                print("    → keyword fallback", file=sys.stderr)

        if buckets is None:
            buckets = build_skills_section_local(r["matched"], country_code)

        lines += format_comment_header(r["score"], country_code, r["title"], r["link"], r["has_desc"])
        lines += render_skills_block(buckets, template)
        lines += ["", " "]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  ✅ Skills tex file saved to: {output_path}")
    print(f"     {len(suitable)} jobs written ({matches} match, {borders} borderline)")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

CV_TEXT_FOR_EMBEDDING = """
Software QA Engineer with experience in test automation using Selenium, Playwright,
Cypress, Python, Java, pytest, Robot Framework, Cucumber BDD, Appium.
CI/CD pipelines with Jenkins, GitLab CI, GitHub Actions, Docker.
API testing with Postman and REST. Agile/Scrum methodology.
Regression testing, exploratory testing, test case design, defect management.
Tools: Jira, Confluence, SQL, Git. End-to-end quality assurance.
"""


def main():
    parser = argparse.ArgumentParser(description="Score job ads against a QA engineer profile")
    parser.add_argument("csv_file")
    parser.add_argument("--title-col",   type=int, default=0)
    parser.add_argument("--desc-col",    type=int, default=2)
    parser.add_argument("--link-col",    type=int, default=1)
    parser.add_argument("--country-col", type=int, default=3)
    parser.add_argument("--output",      type=str, default=None)
    parser.add_argument("--tex",         type=str, default=None)
    parser.add_argument("--verbose",     action="store_true")
    parser.add_argument("--skip-dq",     action="store_true")
    parser.add_argument("--claude",      action="store_true")
    parser.add_argument("--semantic",    action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.csv_file):
        print(f"❌ File not found: {args.csv_file}")
        sys.exit(1)

    jobs = load_csv(args.csv_file, args.title_col, args.desc_col,
                    args.link_col, args.country_col)
    print(f"Loaded {len(jobs)} jobs from {args.csv_file}\n")

    strong_kw, secondary_kw = build_keyword_list()

    sem_model, cv_embedding = None, None
    if args.semantic:
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            print("Loading multilingual embedding model...")
            sem_model    = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            cv_embedding = sem_model.encode([CV_TEXT_FOR_EMBEDDING])[0]
            print("Model loaded.\n")
        except ImportError:
            print("⚠️  sentence-transformers not installed. Falling back to keyword-only.\n")

    results = []
    for job in jobs:
        title, desc = job["title"], job["desc"]
        if is_hard_disqualified(title, desc):
            results.append({
                "score": 0, "verdict": "❌ DQ", "title": title,
                "desc": desc, "link": job["link"], "country": job["country"],
                "matched": [], "sem_score": 0, "has_desc": bool(desc),
            })
            continue

        kw_score, matched, has_desc = score_job(title, desc, strong_kw, secondary_kw)

        if sem_model is not None:
            import numpy as np
            job_text = f"{title} {desc or ''}"
            job_emb  = sem_model.encode([job_text])[0]
            dot      = float(np.dot(cv_embedding, job_emb))
            norm     = float(np.linalg.norm(cv_embedding) * np.linalg.norm(job_emb))
            sem_sc   = int(min(max((dot / norm if norm > 0 else 0) * 100, 0), 100))
            final    = int(0.6 * kw_score + 0.4 * sem_sc)
        else:
            final, sem_sc = kw_score, None

        results.append({
            "score":     final,
            "verdict":   get_verdict(final, has_desc),
            "title":     title,
            "desc":      desc,
            "link":      job["link"],
            "country":   job["country"],
            "matched":   matched,
            "sem_score": sem_sc,
            "has_desc":  has_desc,
        })

    results.sort(key=lambda x: (-x["score"], x["title"]))

    print("=" * 92)
    print(f"  {'SCORE':>6}  {'VERDICT':<16}  FL  JOB TITLE")
    print("=" * 92)
    for r in results:
        if r["verdict"] == "❌ DQ" and not args.skip_dq:
            continue
        score_str    = " DQ" if r["verdict"] == "❌ DQ" else f"{r['score']:>3}%"
        country_code = detect_country(r.get("country", ""))
        flag         = FLAG_MAP.get(country_code, "  ")
        no_desc_mark = "†" if not r.get("has_desc") else " "
        print(f"  [{score_str}]  {r['verdict']:<16}  {flag}{no_desc_mark} {r['title'][:64]}")
        if args.verbose and r["verdict"] not in ("❌ DQ", "❌ SKIP"):
            if r["matched"]:
                print(f"           Matched: {', '.join(r['matched'][:8])}")

    matches     = sum(1 for r in results if r["verdict"] == "✅ MATCH")
    borderlines = sum(1 for r in results if r["verdict"] == "🟡 BORDERLINE")
    skipped     = sum(1 for r in results if r["verdict"] == "❌ SKIP")
    dq          = sum(1 for r in results if r["verdict"] == "❌ DQ")
    no_desc_cnt = sum(1 for r in results if not r.get("has_desc")
                      and r["verdict"] in ("✅ MATCH", "🟡 BORDERLINE"))

    print("=" * 92)
    print(f"\n  ✅ {matches} matches  |  🟡 {borderlines} borderline  |  ❌ {skipped} skipped  |  🚫 {dq} disqualified")
    if no_desc_cnt:
        print(f"  † {no_desc_cnt} of those scored on title only (no description in CSV)")
    print()

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["score", "verdict", "title", "link", "country", "has_desc", "matched_skills"]
            )
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "score":          r["score"],
                    "verdict":        r["verdict"],
                    "title":          r["title"],
                    "link":           r["link"],
                    "country":        r["country"],
                    "has_desc":       r["has_desc"],
                    "matched_skills": "; ".join(r["matched"]),
                })
        print(f"  Results saved to: {args.output}\n")

    if args.tex:
        use_claude = args.claude and bool(os.environ.get("ANTHROPIC_API_KEY"))
        if args.claude and not os.environ.get("ANTHROPIC_API_KEY"):
            print("  ⚠️  --claude set but ANTHROPIC_API_KEY not found. Using keyword fallback.\n")
        write_tex_file(results, args.tex, use_claude=use_claude)


if __name__ == "__main__":
    main()
