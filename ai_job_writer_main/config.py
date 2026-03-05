import os

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
CV_TEX          = os.path.join(BASE_DIR, "sample_cv.tex")
PROMPTS_YAML    = os.path.join(BASE_DIR, "prompts.yaml")
LOCAL_CSV       = os.path.join(BASE_DIR, "jobs", "jobs_March.csv")
OUTPUT_DIR      = os.path.join(BASE_DIR, "output")
OUTPUT_FILE_BASE = os.path.join(OUTPUT_DIR, "Vineet_CV")

# ── RSS Feeds ────────────────────────────────────────────────────────────────
RSS_FEEDS = [
    ("https://rss.app/feeds/1cIR1ioKqvbavRwA.csv", "LinkedIn Playwright/Selenium"),
    ("https://rss.app/feeds/70fRpEBI0ubf6WA2.csv", "LinkedIn Selenium"),
    ("https://rss.app/feeds/Jj5cdbaAJPYnM24X.csv", "StepStone QA"),
]

# ── Gemini API ───────────────────────────────────────────────────────────────
GEMINI_API_KEY   = "key"
GEMINI_API_MODEL = "gemini-2.0-flash"

# ── Local LLM ────────────────────────────────────────────────────────────────
OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3:8b"
OLLAMA_GPU_LAYERS = 18

# ── CDP Chrome ───────────────────────────────────────────────────────────────
CDP_URL = "http://localhost:9222"
# Launch Chrome with:
# "C:\Program Files\Google\Chrome\Application\chrome.exe"
#     --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
