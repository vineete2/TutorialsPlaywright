import re
import time
import requests
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from playwright.sync_api import sync_playwright
import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_API_MODEL, OLLAMA_URL, OLLAMA_MODEL, OLLAMA_GPU_LAYERS, CDP_URL, CV_TEX
from modules.cv_writer import extract_skills_from_reply, save_cv_with_skills

genai.configure(api_key=GEMINI_API_KEY)


def send_to_gemini_api(prompt, output_file="skills.tex"):
    """Send prompt to Gemini REST API."""
    model = genai.GenerativeModel(GEMINI_API_MODEL)
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            reply_text = response.text
            print("\n=== GEMINI API REPLY ===\n", reply_text[:300])
            skills = extract_skills_from_reply(reply_text)
            if skills:
                save_cv_with_skills(skills, output_file)
            else:
                with open("full_reply.txt", "w", encoding="utf-8") as f:
                    f.write(reply_text)
                print("Skills block not found — saved to full_reply.txt")
            return

        except Exception as e:
            err = str(e)
            if "429" in err:
                delay_match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', err)
                wait = int(delay_match.group(1)) + 5 if delay_match else 60
                print(f"⏳ Rate limited — waiting {wait}s (attempt {attempt+1}/3)...")
                time.sleep(wait)
            else:
                print(f"❌ Gemini API error: {e}")
                return


def send_to_local_llm(prompt, output_file="skills.tex", model=None):
    """Send prompt to local Ollama instance."""
    model = model or OLLAMA_MODEL
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_gpu": OLLAMA_GPU_LAYERS,
            "num_predict": 800,
        }
    }
    for attempt in range(3):
        try:
            response = requests.post(OLLAMA_URL, json=data, timeout=300)
            if response.status_code != 200:
                print(f"❌ Ollama error: HTTP {response.status_code}")
                time.sleep(5)
                continue

            reply_data = response.json()
            reply_text = (
                reply_data.get("response", "") or
                reply_data.get("thinking", "") or
                ""
            ).strip()

            if not reply_text:
                print(f"⚠️ Empty response (attempt {attempt+1}/3), retrying in 10s...")
                time.sleep(10)
                continue

            print("\n=== OLLAMA REPLY ===\n", reply_text[:300])
            skills = extract_skills_from_reply(reply_text)
            if skills:
                save_cv_with_skills(skills, output_file)
            else:
                with open("full_reply.txt", "w", encoding="utf-8") as f:
                    f.write(reply_text)
                print("Skills block not found — saved to full_reply.txt")
            return

        except Exception as e:
            print(f"❌ Local LLM error (attempt {attempt+1}/3): {e}")
            time.sleep(10)


def _fill_and_capture_gemini(page, prompt, output_file):
    """Shared Playwright logic: fill prompt, wait for reply, save CV."""

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
        print("Main textbox not found — will use fallback locator")

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
    print("📨 Prompt filled, sending...")

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
    last_text = ""
    stable_count = 0

    while time.time() - start < 90:
        time.sleep(1.8)
        current_text = ""
        try:
            last_reply = page.locator(
                'div.markdown, '
                'div[role="presentation"] div.markdown, '
                '[data-message-author-role="model"] div.markdown'
            ).last
            if last_reply.is_visible():
                current_text = last_reply.inner_text().strip()
        except:
            pass

        if not current_text:
            try:
                model_responses = page.locator('[id^="model-response-message-contentr_"]')
                if model_responses.count() > 0:
                    current_text = model_responses.last.inner_text().strip()
            except:
                pass

        if len(current_text) > 80:
            if current_text == last_text:
                stable_count += 1
                if stable_count >= 2:  # text unchanged for 2 checks = done
                    reply_text = current_text
                    break
            else:
                stable_count = 0
                last_text = current_text

    if not reply_text:
        print("❌ Could not capture reply after 90s")
        return

    print(f"\n=== GEMINI REPLY ({len(reply_text)} chars) ===\n{reply_text[:500]}")

    skills = extract_skills_from_reply(reply_text)
    if skills:
        save_cv_with_skills(skills, output_file)
    else:
        with open("full_reply.txt", "w", encoding="utf-8") as f:
            f.write(reply_text)
        print("Skills block not found — saved to full_reply.txt")


def send_to_gemini(prompt, output_file="skills.tex"):
    """Launch new Playwright browser and use Gemini UI."""
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

#Chrome DevTools Protocol
def send_to_gemini_cdp(prompt, output_file="skills.tex"):
    """Connect to already-open Chrome via CDP and use Gemini UI.

    Launch Chrome first:
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        --remote-debugging-port=9222 --user-data-dir="C:\\chrome-debug"
    Then log into gemini.google.com manually.
    """
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]

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

            # Start new chat to avoid context bleed
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

#Chrome DevTools Protocol
def send_to_grok_cdp(prompt, output_file="skills.tex"):
    """Connect to already-open Chrome via CDP and use Grok UI.
    Make sure x.com/i/grok is already open and logged in.
    """
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]

            grok_page = None
            for page in context.pages:
                if "x.com/i/grok" in page.url or "grok.com" in page.url:
                    grok_page = page
                    break
            if not grok_page:
                grok_page = context.new_page()
                grok_page.goto("https://x.com/i/grok", timeout=30000)
                time.sleep(3)

            grok_page.bring_to_front()
            time.sleep(2)
            grok_page.wait_for_load_state("domcontentloaded")

            # Fill prompt into ProseMirror textbox
            prompt_filled = False
            try:
                textbox = grok_page.locator("div.ProseMirror[contenteditable='true']").first
                textbox.wait_for(state="visible", timeout=15000)
                textbox.click()
                textbox.fill(prompt)
                prompt_filled = True
            except:
                pass

            if not prompt_filled:
                print("❌ Could not find Grok textbox")
                return

            print("📨 Prompt filled, sending...")

            # Send with Enter
            grok_page.keyboard.press("Enter")
            print("Message sent")

            # Wait for stable reply
            print("⏳ Waiting for Grok response...")
            reply_text = ""
            last_text = ""
            stable_count = 0
            start = time.time()

            while time.time() - start < 90:
                time.sleep(1.8)
                current_text = ""
                try:
                    # Target the response-content-markdown div
                    last_reply = grok_page.locator("div.response-content-markdown").last
                    if last_reply.is_visible():
                        current_text = last_reply.inner_text().strip()
                except:
                    pass

                if len(current_text) > 80:
                    if current_text == last_text:
                        stable_count += 1
                        if stable_count >= 2:
                            reply_text = current_text
                            break
                    else:
                        stable_count = 0
                        last_text = current_text

            if not reply_text:
                print("❌ Could not capture Grok reply after 90s")
                return

            print(f"\n=== GROK REPLY ({len(reply_text)} chars) ===\n{reply_text[:500]}")

            # Reuse same extract + save logic
            from modules.cv_writer import extract_skills_from_reply, save_cv_with_skills
            print(f"🔍 Extracting from reply ({len(reply_text)} chars)...")
            skills = extract_skills_from_reply(reply_text)
            if skills:
                save_cv_with_skills(skills, output_file)
                print(f"✅ Saved: {output_file}")
            else:
                print("⚠️ Could not extract skills block — saving raw reply")
                save_cv_with_skills(reply_text, output_file)

        except Exception as e:
            print(f"❌ CDP Grok error: {e}")