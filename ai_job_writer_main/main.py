import os
import sys
import time
from datetime import datetime

# Allow imports from project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config import OUTPUT_FILE_BASE, OUTPUT_DIR
from modules.feed import fetch_and_save_jobs, get_all_jobs, filter_jobs, mark_job_generated, patch_csv_add_generated_column
from modules.cv_writer import build_prompt
from modules.llm import send_to_gemini_api, send_to_gemini_cdp, send_to_gemini, send_to_local_llm
from modules.utils import extract_company

os.makedirs(OUTPUT_DIR, exist_ok=True)

if __name__ == "__main__":
    patch_csv_add_generated_column()
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

        #    Launch Chrome first: "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
        #
        send_to_gemini_cdp(prompt, output_file=out)
        # send_to_gemini_api(prompt, output_file=out)
        # send_to_local_llm(prompt, output_file=out)
        # send_to_gemini(prompt, output_file=out)

        if os.path.exists(out) and os.path.getsize(out) > 500:
            mark_job_generated(title, job.get("Link", ""), out)
            print(f"✅ Marked as generated in CSV")
        else:
            print(f"⚠️ File missing or too small — NOT marked as generated")

        if i < len(jobs) - 1:
            print("  ⏳ Waiting 15s between jobs...")
            time.sleep(15)

    # ── Manual single-job test (comment loop above, uncomment below) ─────────
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
    # send_to_gemini_cdp(prompt, output_file=out)
    # send_to_gemini_api(prompt, output_file=out)
    # send_to_local_llm(prompt, output_file=out)
    # send_to_gemini(prompt, output_file=out)
    # if os.path.exists(out) and os.path.getsize(out) > 500:
    #     mark_job_generated(title, job.get("Link", ""), out)
    #     print(f"✅ Marked as generated in CSV")
    # else:
    #     print(f"⚠️ File missing or too small — NOT marked as generated")
