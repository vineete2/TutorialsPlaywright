import os
import csv
import io
import re
import requests
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

from config import LOCAL_CSV, RSS_FEEDS

GERMAN_REQUIRED_PATTERNS = re.compile(
    r'(?:C1|C2|flie[sß]end|verhandlungssicher|muttersprachlich|native|sehr\s+gute[sn]?)'
    r'(?:[^.]*?(?:deutsch|german))|'
    r'(?:deutsch|german)(?:[^.]*?(?:C1|C2|flie[sß]end|verhandlungssicher|muttersprachlich|native|sehr\s+gute[sn]?))',
    re.IGNORECASE
)


def fetch_and_save_jobs(use_tavily=False):
    """Fetch all RSS feeds, deduplicate globally, append new jobs."""
    seen_links = set()
    existing_rows = []
    existing_fieldnames = None

    os.makedirs(os.path.dirname(LOCAL_CSV), exist_ok=True)

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

    new_rows = []
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

            raw_date = row.get("Date") or row.get("Published") or row.get("pubDate") or ""
            date_only = ""
            if raw_date.strip():
                try:
                    date_only = parsedate_to_datetime(raw_date.strip()).isoformat()
                except Exception:
                    date_only = raw_date.strip()

            raw_desc = row.get("Description") or row.get("Summary") or ""
            plain_desc = re.sub(r"<[^>]+>", " ", raw_desc)
            plain_desc = re.sub(r"\s+", " ", plain_desc).strip()

            clean_row = {
                "Date":        date_only,
                "Title":       row.get("Title", "").strip(),
                "Link":        link,
                "Description": plain_desc,
                "Source":      label,
                "Generated":   "",
            }
            new_rows.append(clean_row)
            added += 1

        print(f"  ✅ {label}: +{added} new (seen total: {len(seen_links)})")

    if not new_rows:
        print("No new jobs found. CSV unchanged.")
        return

    all_rows = existing_rows + new_rows
    with open(LOCAL_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Date", "Title", "Link", "Description", "Source", "Generated"],
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(all_rows)

    # # Optionally add Tavily results
    # if use_tavily:
    #     try:
    #         from modules.tavily_feed import fetch_tavily_jobs
    #         print("Fetching via Tavily search...")
    #         tavily_jobs = fetch_tavily_jobs()
    #         for job in tavily_jobs:
    #             link = job.get("Link", "")
    #             if link and link not in seen_links:
    #                 seen_links.add(link)
    #                 new_rows.append(job)
    #         print(f"  ✅ Tavily added {len(tavily_jobs)} candidates")
    #     except Exception as e:
    #         print(f"  ⚠️ Tavily feed failed: {e}")

    print(f"\n✅ Appended {len(new_rows)} new jobs → {LOCAL_CSV} now has {len(all_rows)} total")


def get_all_jobs():
    """Return only jobs not yet generated."""
    filtered = []
    skipped = 0
    with open(LOCAL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Generated", "").strip():
                skipped += 1
                continue
            filtered.append(row)
    print(f"→ {len(filtered)} unprocessed jobs, {skipped} already generated.")
    return filtered


def filter_jobs(jobs):
    """Filter out jobs requiring C1+ German and jobs older than 24 hours."""
    cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    print(f"  🕐 Cutoff: {cutoff_24h.strftime('%Y-%m-%d %H:%M')} UTC")
    filtered = []
    for job in jobs:
        date_str = job.get("Date", "").strip()
        if date_str:
            try:
                pub_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if pub_date < cutoff_24h:
                    print(f"  ⏭ Skipping old ({date_str[:10]}): {job.get('Title','')[:60]}")
                    continue
            except Exception:
                pass
        desc = job.get("Description", "") + " " + job.get("Title", "")
        if GERMAN_REQUIRED_PATTERNS.search(desc):
            print(f"  🇩🇪 Skipping (German C1+ required): {job.get('Title','')[:60]}")
            continue
        filtered.append(job)
    print(f"→ {len(filtered)} jobs after filters ({len(jobs) - len(filtered)} skipped)")
    return filtered


def mark_job_generated(title, link, output_file):
    """Mark a job as generated in the CSV."""
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


def patch_csv_add_generated_column():
    """One-time migration: add Generated column to existing CSV rows."""
    if not os.path.exists(LOCAL_CSV):
        return
    rows = []
    with open(LOCAL_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "Generated" not in row:
                row["Generated"] = ""
            rows.append(row)
    with open(LOCAL_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Date", "Title", "Link", "Description", "Source", "Generated"],
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)
    print("✅ CSV patched with Generated column")
