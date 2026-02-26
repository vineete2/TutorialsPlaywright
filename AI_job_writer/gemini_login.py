from playwright.sync_api import sync_playwright
import time

from AI_job_writer.auto_grok_job import extract_skills_from_reply, OUTPUT_FILE


def send_to_gemini_sample(prompt: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)  # slow_mo so you can watch
        context = browser.new_context()
        page = context.new_page()

        print("Navigating to Gemini...")

        page.goto("https://gemini.google.com/")

        # Step 1: Handle consent if it appears (timeout 8 seconds)
        print("Checking for consent screen...")
        try:
            reject_btn = page.get_by_role("button", name="Reject all")
            reject_btn.wait_for(state="visible", timeout=8000)
            reject_btn.click()
            print("Clicked 'Reject all'")
            page.wait_for_load_state("networkidle")
        except:
            print("No consent screen detected (already accepted or skipped)")

        # Step 2: Wait for the real prompt box
        print("Waiting for prompt input box...")
        try:
            # Most reliable locator for Gemini input in 2025
            prompt_box = page.get_by_role("textbox", name="Enter a prompt for Gemini")
            prompt_box.wait_for(state="visible", timeout=15000)

            # Click & fill
            prompt_box.click()
            prompt_box.fill(prompt)
            print("Prompt filled successfully")

            # Send
            send_btn = page.get_by_role("button", name="Send message")
            send_btn.wait_for(state="visible", timeout=5000)
            send_btn.click()
            print("Message sent")

        except Exception as e:
            print("Could not find/fill prompt box:", str(e))
            # Fallback locator (sometimes used)
            try:
                page.locator("rich-textarea div").nth(1).fill(prompt)
                page.get_by_role("button", name="Send message").click()
                print("Used fallback locator")
            except:
                print("Fallback also failed – check browser manually")

        # Wait a bit to see the reply (optional – remove later)
        print("Waiting 12 seconds to see the reply...")
        page.wait_for_timeout(12000)

        print("Closing browser in 5 seconds...")
        page.wait_for_timeout(5000)
        browser.close()


def send_to_gemini(prompt):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=80)
        context = browser.new_context()
        page = context.new_page()

        print("Opening Gemini...")

        page.goto("https://gemini.google.com/")

        # Handle consent screen if it shows up
        print("Checking for consent screen...")
        try:
            reject_btn = page.get_by_role("button", name="Reject all")
            reject_btn.wait_for(state="visible", timeout=8000)
            reject_btn.click()
            print("Clicked 'Reject all'")
            page.wait_for_load_state("networkidle", timeout=10000)
        except:
            print("No consent screen (already skipped or accepted)")

        # Wait for the prompt input box
        print("Waiting for prompt input...")
        input_box = page.get_by_role("textbox", name="Enter a prompt for Gemini")
        input_box.wait_for(state="visible", timeout=15000)

        # Fill and send
        input_box.click()
        input_box.fill(prompt)
        print("Prompt filled")

        send_button = page.get_by_role("button", name="Send message")
        send_button.click()
        print("Message sent")

        # Wait for reply (dynamic, stops early)
        print("Waiting for Gemini reply...")
        start = time.time()
        reply_text = None

        while time.time() - start < 30:
            try:
                # Reliable Gemini reply locator
                reply = page.locator('.markdown, div[role="presentation"] div.markdown, .response-container').last
                if reply.is_visible():
                    reply_text = reply.inner_text().strip()
                    if len(reply_text) > 150:  # reasonable length for real answer
                        break
            except:
                pass
            time.sleep(1.5)

        if reply_text:
            print("\n=== GEMINI REPLY ===\n")
            print(reply_text)

            # Extract & save skills
            skills_latex = extract_skills_from_reply(reply_text)
            if skills_latex:
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    f.write(skills_latex)
                print(f"\nSaved rewritten skills to: {OUTPUT_FILE}")
            else:
                print("Could not extract skills block")
                with open("full_reply.txt", "w", encoding="utf-8") as f:
                    f.write(reply_text)
        else:
            print("No reply detected automatically — check browser manually")

        input("\nPress Enter to close browser...")
        browser.close()

# Example run
if __name__ == "__main__":
    test_prompt = "Write a short haiku about Python programming"
    send_to_gemini(test_prompt)
    send_to_gemini_sample(test_prompt)
