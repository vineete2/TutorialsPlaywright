# AI Job Writer

This project is an AI-powered tool for automating job application processes. It fetches job listings from RSS feeds, filters them, extracts relevant skills, and generates tailored CVs using large language models (LLMs) like Gemini, CDP, Ollama, or Playwright for browser automation.

## Project Structure

```
ai_job_writer/
├── main.py           ← Entry point; run this to start the application
├── config.py         ← Contains all constants, API keys, and paths
├── prompts.yaml      ← YAML file for storing prompts used in LLM interactions
├── sample_cv.tex     ← Sample CV template in LaTeX format
├── photo.jpg         ← Sample photo for CV inclusion (e.g., profile picture)
├── jobs/
│   └── jobs_March.csv ← CSV file storing fetched and filtered job listings
├── output/
│   └── Vineet_CV_*.tex ← Generated output CV files (e.g., tailored LaTeX CVs)
└── modules/
    ├── feed.py       ← Handles RSS fetching, filtering, and CSV management
    ├── cv_writer.py  ← Extracts skills, builds prompts for CV generation
    ├── llm.py        ← Interfaces with LLMs (Gemini API, CDP, Ollama, Playwright)
    └── utils.py      ← Utility functions (e.g., extract_company)
```

## Setup

1. **Clone the Repository** (if applicable) or create the directory structure as shown above.

2. **Copy Required Files**:
    - Place your custom `prompts.yaml` in the root directory.
    - Place your base CV template as `sample_cv.tex` in the root directory.
    - Place your profile photo as `photo.jpg` in the root directory.
    - If you have existing job data, copy `jobs_March.csv` (or similar) into the `jobs/` directory.

3. **Install Dependencies**:
    - Ensure Python 3.x is installed.
    - Install required packages via pip:
      ```
      pip install requests feedparser pyyaml google-generativeai playwright  # Add others as needed (e.g., ollama)
      ```
    - For Playwright, run:
      ```
      playwright install
      ```

4. **Configure API Keys**:
    - Edit `config.py` to add your API keys (e.g., for Gemini or other services).

## Usage

1. Run the application:
   ```
   python main.py
   ```

2. The script will:
    - Fetch job listings from RSS feeds (configured in `feed.py`).
    - Filter and save them to `jobs/jobs_March.csv` (or similar).
    - Extract skills and build prompts using `cv_writer.py`.
    - Use LLMs via `llm.py` to generate tailored CVs.
    - Output generated CVs to the `output/` directory.

## Migration from Previous Version

If migrating from an older version (e.g., using `feed2.py`):

1. Copy `sample_cv.tex`, `photo.jpg`, and `prompts.yaml` into the new root folder.

2. Copy your existing `jobs_March.csv` into the `jobs/` directory.

3. Use `python main.py` as the new entry point instead of `python feed2.py`.

4. Keep `feed2.py` as a backup until the new setup is confirmed working.

## Notes

- This tool creates files, runs commands, and reads files as part of its operation (e.g., creating 7 files, running 3 commands, reading a file).
- Customize prompts in `prompts.yaml` for better CV tailoring.
- Ensure compliance with job site terms of service when fetching RSS feeds.
- For debugging, check logs or add print statements in the modules.

## Contributing

Feel free to fork and submit pull requests for improvements!