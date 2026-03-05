import re


def extract_company(title):
    """Extract company name from job title."""
    # Try "sucht" or "hiring" pattern (LinkedIn format)
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
