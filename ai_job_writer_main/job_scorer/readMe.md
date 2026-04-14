"""
job_scorer.py — Multilingual Job Ad Scorer for Software QA/Test Engineers
==========================================================================
Author: Vineet (with Claude)

HOW IT WORKS — THE FULL PICTURE
---------------------------------
This script reads a CSV of job ads and scores each one against a hardcoded
skill profile (yours). It uses a combination of:

1. KEYWORD MATCHING (the core engine)
    - Searches the job title + description for known skills/tools
    - Two tiers: STRONG skills (core QA/test tools) and SECONDARY skills
    - Each match adds weighted points to a raw score

2. WEIGHTED SCORING (not ML — pure rule-based)
    - Title bonus: +15 pts if the title contains QA/test-related words
      (jobs titled "QA Engineer" are more relevant than random matches)
    - Strong skill hit: +10 pts each  (Selenium, Playwright, pytest, etc.)
    - Secondary skill hit: +5 pts each (SQL, Jira, Git, etc.)
    - English requirement bonus: +5 pts (useful for non-English-speaking countries)
    - Seniority penalty: -15 pts for "Head of / VP / 10+ years"
      -5 pts for "Senior / Lead / 5+ years"
    - Raw score is capped at 0–100 via min/max

3. HARD DISQUALIFIERS (blocklist)
    - Certain keywords in title or description immediately mark a job as DQ
    - These represent entirely different domains: mechanical QA, oil & gas,
      embedded HW testing, internships, etc.
    - Checked BEFORE scoring to save time

4. VERDICT THRESHOLDS
    - ≥ 55%  → ✅ MATCH     (apply)
    - 35–54% → 🟡 BORDERLINE (read carefully)
    - < 35%  → ❌ SKIP

WHY NOT ML / NLP?
------------------
The original script uses NO machine learning, no embeddings, no transformers.
It's entirely rule-based. This is actually fine for a personal job search tool
because:
- You know exactly which skills you have
- You can tune weights yourself
- It runs instantly with zero dependencies
- It's 100% explainable

THE MULTILINGUAL PROBLEM
-------------------------
Job ads from Germany, France, Norway etc. use different words for the same
role. This script handles it two ways:

METHOD A (default, offline): Multilingual keyword dictionaries
- You manually add translations of key terms to MULTILANG_SYNONYMS below
- Fast, zero dependencies, fully adjustable
- Example: "test automation" → also match "testautomatisierung" (DE),
"automatisation des tests" (FR), "testautomatisering" (NO/SE)

METHOD B (optional, offline after setup): Sentence Embeddings
- Uses the `sentence-transformers` library with model
`paraphrase-multilingual-MiniLM-L12-v2`
- Model is ~500MB, downloads once, then works fully offline
- Converts your CV skills and each job description into semantic vectors
- Computes cosine similarity — so "Entwickler" and "developer" score
similarly without you listing every translation
- Enable with: --semantic flag (see CLI usage below)
- Install: pip install sentence-transformers

USAGE
------
Basic:
python3 job_scorer.py jobs.csv

With semantic scoring (multilingual embeddings):
python3 job_scorer.py jobs.csv --semantic

Custom column indices (0-based):
python3 job_scorer.py jobs.csv --title-col 0 --desc-col 2 --link-col 3

Save results to CSV:
python3 job_scorer.py jobs.csv --output results.csv

Show full description for matches:
python3 job_scorer.py jobs.csv --verbose

INPUT CSV FORMAT
-----------------
Expected columns (adjust with flags if different):
Column 0: Job Title
Column 1: (anything, e.g. company)
Column 2: Job Description
Column 3: Link (optional)

ADJUSTING FOR YOUR OWN PROFILE
--------------------------------
1. Edit STRONG_SKILLS and SECONDARY_SKILLS below
2. Edit HARD_DISQUALIFIERS to block irrelevant domains
3. Edit MULTILANG_SYNONYMS to add translations
4. Adjust MATCH_THRESHOLD and BORDERLINE_THRESHOLD
5. Change point values in the score() function
   """