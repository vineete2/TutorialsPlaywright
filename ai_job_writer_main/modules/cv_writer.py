import re
import yaml

from config import CV_TEX, PROMPTS_YAML


def load_resume(path=None):
    """Extract and clean the Skills section from sample_cv.tex."""
    path = path or CV_TEX
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.search(r'\\section\*\{Skills\}.*?(?=\\section|\Z)', content, re.DOTALL)
        if match:
            skills_raw = match.group(0)
            skills_raw = re.sub(r'\\textbf\{([^}]+)\}', r'\1', skills_raw)
            skills_raw = re.sub(r'\\begin\{[^}]+\}|\\end\{[^}]+\}', '', skills_raw)
            skills_raw = re.sub(r'\\item', '-', skills_raw)
            skills_raw = re.sub(r'\\[a-zA-Z]+\*?\{[^}]*\}', '', skills_raw)
            skills_raw = re.sub(r'\\[a-zA-Z]+', '', skills_raw)
            skills_raw = re.sub(r'[{}]', '', skills_raw)
            # Remove LaTeX comments (% to end of line)
            skills_raw = re.sub(r'\s*%[^\n]*', '', skills_raw)
            skills_raw = re.sub(r'\\&', '&', skills_raw)
            skills_raw = re.sub(r'\\_', '_', skills_raw)
            skills_raw = re.sub(r'\\%', '%', skills_raw)
            skills_raw = re.sub(r'\n\s*\n+', '\n', skills_raw).strip()
            print(f"📋 Loaded skills ({len(skills_raw)} chars):\n{skills_raw}\n--- END ---")
            return skills_raw
        else:
            print("⚠️ Skills section not found in tex file — loading full text")
            return content
    except FileNotFoundError:
        print(f"❌ Resume file not found: {path}")
        exit(1)


def load_prompts(path=None):
    path = path or PROMPTS_YAML
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Load once at import time
RESUME = load_resume()
PROMPTS = load_prompts()


def build_prompt(job, job_num):
    template = PROMPTS["prompts"]["build_cv_skills"]
    desc = job.get("Description", "").strip()
    link = job.get("Link", "").strip()
    title = job.get("Title", "No title")

    if len(desc.splitlines()) < 3 or len(desc) < 150:
        desc = f"Visit this URL and read the full job description before rewriting skills: {link}"

    return (
        template
        .replace("$resume", f"My current skills:\n{RESUME}")
        .replace("$title", title)
        .replace("$desc", desc)
    )


def remove_languages_from_skills(skills_block):
    lang_patterns = [
        r'\\item\s*\\textbf\{[^}]*[Ll]anguages[^}]*\}[:\s]*.*?(?=\\item|\\end\{itemize\})',
        r'\\item\s*English\s*[\(\[].*?[\)\]].*?(?=\\item|\\end\{itemize\})',
        r'\s*\\textbf\{[Ll]anguages[^}]*\}[:\s]*[^\\\n]*(?:\\\\)?',
    ]
    for pat in lang_patterns:
        skills_block = re.sub(pat, '', skills_block, flags=re.I | re.DOTALL)
    return skills_block


def clean_skills_block(skills_block):
    # Remove Technical Skills sub-header
    skills_block = re.sub(
        r'(?m)^\s*(?:\\subsection\*?\s*\{Technical Skills\}|\\textbf\{Technical Skills\})\s*\\?\s*$',
        '', skills_block, flags=re.I
    )
    skills_block = re.sub(r'(?m)^\s*Technical Skills\s*\\?\s*$', '', skills_block, flags=re.I)

    # Fix \textbf{Label: rest} → \textbf{Label:} rest
    def fix_textbf(m):
        inner = m.group(1)
        colon_pos = inner.find(':')
        if colon_pos == -1:
            return m.group(0)
        label = inner[:colon_pos + 1]
        rest = inner[colon_pos + 1:]
        if rest.strip():
            return r'\textbf{' + label + '}' + rest
        return m.group(0)

    skills_block = re.sub(r'\\textbf\{([^}]+)\}', fix_textbf, skills_block)

    # Escape bare & inside \textbf{} labels
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
        return skills_block

    fallback_lines = (
        '\\item \\textbf{Programming \\& Scripting:} Java, SQL querying, test automation frameworks\n'
        '\\item \\textbf{Database:} Oracle PL/SQL, MongoDB\n'
    )
    new_block = re.sub(r'(\\end\{itemize\})', fallback_lines + r'\1', skills_block, count=1)
    if new_block == skills_block:
        new_block = skills_block.rstrip() + '\n' + fallback_lines
    return new_block


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
    """Extract the skills block from LLM reply. Handles Mistral, Gemini, Ollama formats."""
    print(f"🔍 Extracting from reply ({len(reply_text)} chars)...")
    print(f"📄 Reply preview:\n{reply_text[:500]}\n")
    # 1. Unwrap \begin{verbatim}
    reply_text = re.sub(
        r'\\begin\{verbatim\}(.*?)\\end\{verbatim\}',
        lambda m: m.group(1), reply_text, flags=re.DOTALL
    )
    # 2. Strip \documentclass preamble
    reply_text = re.sub(r'(?s)\\documentclass.*?\\begin\{document\}', '', reply_text)
    reply_text = re.sub(r'\\end\{document\}', '', reply_text)
    # 3. Strip markdown code fences
    reply_text = re.sub(r'```(?:latex|tex)?\s*(.*?)\s*```', lambda m: m.group(1), reply_text, flags=re.DOTALL)
    # 4. Strip <think> blocks (qwen3)
    reply_text = re.sub(r'<think>.*?</think>', '', reply_text, flags=re.DOTALL)
    # 5. Fix hallucinated commands like \Checklist
    reply_text = re.sub(
        r'\\(?!item|textbf|begin|end|section|subsection|hfill|textit|href)[A-Za-z]+:',
        r'\\item \\textbf{Tools \\& Stack:}', reply_text
    )
    # 6. Remove inline model commentary
    reply_text = re.sub(r'\((?:addendum|note|consider|tip|suggestion)[^)]*\)', '', reply_text, flags=re.I)

    content = None

    # Strategy A: \section*{Skills}
    m = re.search(
        r'(?is)\\section\*\s*\{(?:Skills|Technical Skills)\}.*?(?=\\section|\Z)',
        reply_text, re.DOTALL
    )
    if m:
        content = m.group(0).strip()

    # Strategy B: \begin{itemize}...\end{itemize}
    if not content:
        m = re.search(r'(?is)\\begin\{itemize\}.*?\\end\{itemize\}', reply_text, re.DOTALL)
        if m:
            content = m.group(0).strip()

    # Strategy C: enumerate → itemize
    if not content:
        m = re.search(r'(?is)\\begin\{enumerate\}.*?\\end\{enumerate\}', reply_text, re.DOTALL)
        if m:
            content = m.group(0).strip()
            content = content.replace(r'\begin{enumerate}', r'\begin{itemize}')
            content = content.replace(r'\end{enumerate}', r'\end{itemize}')

    # Strategy D: bare \textbf lines
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

    # Normalisation
    content = re.sub(r'(?<!\\)\\(?!\\|\w|\{)(\s*\n)', r'\\\\\1', content)
    content = re.sub(r'(Updated|New|Initial)\s*(Match|Score|Analysis).*', '', content, flags=re.I | re.DOTALL)
    content = re.sub(r'\\small\s*\{([^}]*)\}', r'\1', content)
    content = re.sub(r'\\item\s*\{([^}]*)\}\s*\{', r'\\item \1 {', content)
    #content = remove_languages_from_skills(content)
    content = clean_skills_block(content)

    # Wrap in itemize if needed
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

    content = inject_programming_fallback(content)
    content = dedup_skills(content)

    content = re.sub(r'\n\s*\n+', '\n', content)
    content = content.strip()

    if len(content) < 80 or r'\end{itemize}' not in content:
        print("Extracted content looks too short or broken → discarding")
        return None

    return content


def save_cv_with_skills(skills, output_file):
    """Inject skills block into sample_cv.tex and save to output_file."""
    skills_esc = skills.replace('\\', '\\\\')
    with open(CV_TEX, "r", encoding="utf-8") as f:
        cv = f.read()
    new_cv = re.sub(
        r'(?:\\section\*\s*\{Skills\}.*?)+(?=\\section|\Z)',
        skills_esc + '\n',
        cv, count=1, flags=re.DOTALL | re.MULTILINE
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_cv)
    print(f"✅ Saved: {output_file}")
