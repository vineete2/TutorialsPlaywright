
import csv
import io
import sys
import argparse
import os
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — Edit this section to match YOUR profile
# ─────────────────────────────────────────────────────────────────────────────

# Core skills — each match adds 10 points
STRONG_SKILLS = [
    "selenium", "playwright", "cypress", "python", "java",
    "ci/cd", "jenkins", "gitlab", "cucumber", "bdd",
    "agile", "scrum", "postman", "api", "regression", "exploratory",
    "docker", "github actions", "test automation", "quality assurance",
    "qa", "robot framework", "pytest", "e2e", "end-to-end", "appium",
]

# Supporting skills — each match adds 5 points
SECONDARY_SKILLS = [
    "testng", "jest", "maven", "javascript", "typescript",
    "spring boot", "c#", "azure devops", "linux", "git", "devops",
    "rest", "graphql", "kanban", "functional", "test case",
    "test plan", "defect", "jira", "confluence", "sql",
]

# Jobs containing ANY of these → immediately disqualified (score = 0, skipped)
# Add domain-specific terms you never want to see
HARD_DISQUALIFIERS = [
    # Wrong engineering domains
    "mechanical engineer", "subsea", "oil and gas", "plumbing",
    "electrical qc", "qc engineer", "manufacturing qa", "manufacturing qc",
    "commissioning engineer ertms", "railway signal", "jernbanesignal",
    "hardware qa", "embedded test", "hw qa", "pcb", "iec 62304",
    "e&p engineer", "m&p engineer",
    # Career level mismatches
    "intern", "internship", "vikariat",
    "head of engineering productivity",
    # Specific known mismatches (can remove these)
    "2d document processing",
]

# Multilingual synonym map — keys are your base English terms,
# values are lists of translations to also match.
# This solves the "same job, different language" problem WITHOUT any ML.
MULTILANG_SYNONYMS = {
    # German
    "test automation":    ["testautomatisierung", "test-automatisierung"],
    "quality assurance":  ["qualitätssicherung", "qualitätskontrolle", "qualitaetssicherung"],
    "software testing":   ["softwaretest", "softwaretesting", "softwareprüfung"],
    "regression":         ["regressionstests", "regressionstest"],
    "agile":              ["agiles", "agilität"],
    "scrum":              ["scrum-master"],
    "defect":             ["fehler", "bug", "fehlerbericht"],
    "test case":          ["testfall", "testfälle"],
    "test plan":          ["testplan", "testplanung"],
    "continuous integration": ["kontinuierliche integration"],

    # French
    "quality assurance":  ["assurance qualité", "assurance-qualité", "contrôle qualité"],
    "test automation":    ["automatisation des tests", "automatisation de test"],
    "software testing":   ["test logiciel", "tests logiciels"],
    "regression":         ["tests de régression", "régression"],
    "defect":             ["défaut", "anomalie", "bogue"],
    "agile":              ["méthodologie agile"],
    "test case":          ["cas de test", "cas d'essai"],

    # Norwegian / Swedish / Danish
    "test automation":    ["testautomatisering", "test-automatisering"],
    "quality assurance":  ["kvalitetssikring", "kvalitetssäkring", "kvalitetskontroll"],
    "software testing":   ["programvaretesting", "mjukvarutestning"],
    "regression":         ["regresjonstest", "regressionstest"],
    "defect":             ["feil", "defekt", "bug"],
    "agile":              ["smidig", "agil utvikling"],
    "scrum":              ["scrum-team"],
    "test case":          ["testtilfelle", "testfall"],
}

# ─────────────────────────────────────────────────────────────────────────────
# SCORING THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────────

MATCH_THRESHOLD      = 55   # >= this → ✅ MATCH
BORDERLINE_THRESHOLD = 35   # >= this → 🟡 BORDERLINE, else ❌ SKIP

# Maximum raw points possible (used for normalization).
# This is approximately: title bonus (15) + 26 strong skills * 10 + 20 secondary * 5
# Keep this roughly equal to your realistic maximum score.
MAX_RAW_POINTS = 100


# ─────────────────────────────────────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def build_keyword_list():
    """
    Expand STRONG and SECONDARY skill lists with multilingual synonyms.
    Returns two lists: (strong_expanded, secondary_expanded)
    each containing (keyword, points) tuples.
    """
    strong_expanded = [(sk, 10) for sk in STRONG_SKILLS]
    secondary_expanded = [(sk, 5) for sk in SECONDARY_SKILLS]

    for base_term, translations in MULTILANG_SYNONYMS.items():
        # Determine which tier the base term belongs to
        if base_term in STRONG_SKILLS:
            tier = strong_expanded
            pts = 10
        else:
            tier = secondary_expanded
            pts = 5
        for t in translations:
            tier.append((t, pts))

    return strong_expanded, secondary_expanded


def is_hard_disqualified(title: str, desc: str) -> bool:
    """Return True if ANY hard disqualifier appears in title or description."""
    combined = (title + " " + (desc or "")).lower()
    return any(kw in combined for kw in HARD_DISQUALIFIERS)


def score_job(title: str, desc: str,
              strong_keywords, secondary_keywords) -> tuple[int, list[str]]:
    """
    Score a job against the candidate's profile.

    Returns:
        (score_0_to_100, list_of_matched_skills)

    Scoring breakdown:
        +15  if title/desc contains 'qa', 'quality assurance', 'test', 'tester', 'testing'
        +10  per STRONG skill match
        +5   per SECONDARY skill match
        +5   if English fluency is explicitly required (useful for non-EN countries)
        -15  if very senior (Head of, VP, 10+ years, Principal)
        -5   if senior/lead (Senior, Lead, 5+ years)
    """
    combined = (title + " " + (desc or "")).lower()
    raw_pts = 0
    matched = []

    # Title/role type bonus — confirms this is actually a QA/test job
    if any(k in combined for k in ["qa", "quality assurance", "test", "tester", "testing"]):
        raw_pts += 15

    # Skill matches
    for kw, pts in strong_keywords:
        if kw in combined:
            raw_pts += pts
            matched.append(f"{kw}(+{pts})")

    for kw, pts in secondary_keywords:
        if kw in combined:
            raw_pts += pts
            matched.append(f"{kw}(+{pts})")

    # English language bonus — helps filter international roles where English is ok
    if any(k in combined for k in ["english required", "english fluent",
                                   "fluency in english", "must speak english",
                                   "english speaking", "english is required"]):
        raw_pts += 5

    # Seniority penalties — you're mid-level, not a head/VP/principal
    if any(k in combined for k in ["10+ years", "8+ years", "head of", "vp of",
                                   "principal engineer", "senior lead"]):
        raw_pts -= 15
    elif any(k in combined for k in ["senior", "5+ years", "5 years", "lead "]):
        raw_pts -= 5

    # Normalize to 0–100
    normalized = int((raw_pts / MAX_RAW_POINTS) * 100)
    return min(max(normalized, 0), 100), matched


def get_verdict(score: int) -> str:
    if score >= MATCH_THRESHOLD:
        return "✅ MATCH"
    elif score >= BORDERLINE_THRESHOLD:
        return "🟡 BORDERLINE"
    else:
        return "❌ SKIP"


# ─────────────────────────────────────────────────────────────────────────────
# OPTIONAL: SEMANTIC SCORING (sentence-transformers)
# ─────────────────────────────────────────────────────────────────────────────

def semantic_score(title: str, desc: str, model, cv_embedding) -> int:
    """
    Compute cosine similarity between a job ad and the CV embedding.
    Returns 0–100. Only called if --semantic flag is set.

    The model `paraphrase-multilingual-MiniLM-L12-v2`:
    - Supports 50+ languages including DE, FR, NO, SV, DA
    - Runs fully offline after first download (~500MB)
    - Maps text to 384-dimensional semantic vectors
    - Cosine similarity near 1.0 = very similar meaning
    """
    import numpy as np
    job_text = f"{title} {desc or ''}"
    job_emb = model.encode([job_text])[0]
    # Cosine similarity
    dot = float(np.dot(cv_embedding, job_emb))
    norm = float(np.linalg.norm(cv_embedding) * np.linalg.norm(job_emb))
    similarity = dot / norm if norm > 0 else 0.0
    return int(min(max(similarity * 100, 0), 100))


CV_TEXT_FOR_EMBEDDING = """
Software QA Engineer with experience in test automation using Selenium, Playwright,
Cypress, Python, Java, pytest, Robot Framework, Cucumber BDD, Appium.
CI/CD pipelines with Jenkins, GitLab CI, GitHub Actions, Docker.
API testing with Postman and REST. Agile/Scrum methodology.
Regression testing, exploratory testing, test case design, defect management.
Tools: Jira, Confluence, SQL, Git. End-to-end quality assurance.
"""


# ─────────────────────────────────────────────────────────────────────────────
# CSV LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_csv(filepath: str, title_col: int, desc_col: int, link_col: int) -> list[dict]:
    """Load job ads from CSV, returning list of dicts with title/desc/link."""
    raw = open(filepath, encoding="utf-8-sig", errors="replace").read()
    jobs = []
    for i, row in enumerate(csv.reader(io.StringIO(raw))):
        if i == 0 and row[title_col].strip().lower() in ["title", "job title", "jobtitle"]:
            continue  # skip header
        if len(row) <= max(title_col, desc_col):
            continue
        title = row[title_col].strip()
        desc  = row[desc_col].strip()
        link  = row[link_col].strip() if len(row) > link_col else ""
        if title:
            jobs.append({"title": title, "desc": desc, "link": link})
    return jobs


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Score job ads against a QA engineer profile"
    )
    parser.add_argument("csv_file", help="Path to your jobs CSV file")
    parser.add_argument("--title-col",  type=int, default=0, help="Column index for job title (default: 0)")
    parser.add_argument("--desc-col",   type=int, default=2, help="Column index for description (default: 2)")
    parser.add_argument("--link-col",   type=int, default=3, help="Column index for link (default: 3)")
    parser.add_argument("--output",     type=str, default=None, help="Save results to this CSV file")
    parser.add_argument("--verbose",    action="store_true", help="Show matched keywords and description snippet")
    parser.add_argument("--semantic",   action="store_true",
                        help="Add semantic (multilingual embedding) scoring. Requires: pip install sentence-transformers")
    parser.add_argument("--skip-dq",    action="store_true", help="Show disqualified jobs too (with DQ label)")
    args = parser.parse_args()

    if not os.path.exists(args.csv_file):
        print(f"❌ File not found: {args.csv_file}")
        sys.exit(1)

    # Load jobs
    jobs = load_csv(args.csv_file, args.title_col, args.desc_col, args.link_col)
    print(f"Loaded {len(jobs)} jobs from {args.csv_file}\n")

    # Build keyword lists (with multilingual expansions)
    strong_kw, secondary_kw = build_keyword_list()

    # Optional: load semantic model
    sem_model = None
    cv_embedding = None
    if args.semantic:
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            print("Loading multilingual embedding model (first run downloads ~500MB)...")
            sem_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            cv_embedding = sem_model.encode([CV_TEXT_FOR_EMBEDDING])[0]
            print("Model loaded.\n")
        except ImportError:
            print("⚠️  sentence-transformers not installed. Run: pip install sentence-transformers")
            print("Falling back to keyword-only scoring.\n")

    # Score all jobs
    results = []
    for job in jobs:
        title, desc = job["title"], job["desc"]

        if is_hard_disqualified(title, desc):
            results.append({
                "score": 0, "verdict": "❌ DQ", "title": title,
                "desc": desc, "link": job["link"], "matched": [], "sem_score": 0
            })
            continue

        kw_score, matched = score_job(title, desc, strong_kw, secondary_kw)

        # Combine keyword + semantic scores if enabled
        if sem_model is not None:
            sem_sc = semantic_score(title, desc, sem_model, cv_embedding)
            # Blend: 60% keyword (tunable), 40% semantic
            final_score = int(0.6 * kw_score + 0.4 * sem_sc)
        else:
            final_score = kw_score
            sem_sc = None

        results.append({
            "score": final_score,
            "verdict": get_verdict(final_score),
            "title": title,
            "desc": desc,
            "link": job["link"],
            "matched": matched,
            "sem_score": sem_sc,
        })

    results.sort(key=lambda x: (-x["score"], x["title"]))

    # ── Print to terminal ──────────────────────────────────────────────────
    print("=" * 90)
    print(f"  {'SCORE':>6}  {'VERDICT':<16}  JOB TITLE")
    print("=" * 90)

    for r in results:
        if r["verdict"] == "❌ DQ" and not args.skip_dq:
            continue  # hide DQs from terminal unless requested
        score_str = " DQ" if r["verdict"] == "❌ DQ" else f"{r['score']:>3}%"
        print(f"  [{score_str}]  {r['verdict']:<16}  {r['title'][:70]}")

        if args.verbose and r["verdict"] != "❌ DQ":
            if r["matched"]:
                print(f"           Matched: {', '.join(r['matched'][:8])}")
            if r["sem_score"] is not None:
                print(f"           Semantic score: {r['sem_score']}%")
            if r["desc"]:
                print(f"           → {r['desc'][:120]}...")
            print()

    # Summary
    matches     = sum(1 for r in results if r["verdict"] == "✅ MATCH")
    borderlines = sum(1 for r in results if r["verdict"] == "🟡 BORDERLINE")
    skipped     = sum(1 for r in results if r["verdict"] == "❌ SKIP")
    dq          = sum(1 for r in results if r["verdict"] == "❌ DQ")

    print("=" * 90)
    print(f"\n  ✅ {matches} matches  |  🟡 {borderlines} borderline  |  ❌ {skipped} skipped  |  🚫 {dq} disqualified\n")

    # ── Save to CSV if requested ───────────────────────────────────────────
    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["score", "verdict", "title", "link", "matched_skills"])
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "score": r["score"],
                    "verdict": r["verdict"],
                    "title": r["title"],
                    "link": r["link"],
                    "matched_skills": "; ".join(r["matched"]),
                })
        print(f"  Results saved to: {args.output}\n")


if __name__ == "__main__":
    main()