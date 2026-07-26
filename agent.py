import os
import requests
from bs4 import BeautifulSoup
from groq import Groq
from playwright.sync_api import sync_playwright

IXAMBEE_URL = "https://www.ixambee.com/upcoming-government-exams"

def scrape_ixambee_content():
    """Scrape ixamBee page using Playwright stealth configurations."""
    try:
        with sync_playwright() as p:
            # Launch chromium with anti-bot flags
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1366, 'height': 768},
                locale="en-US"
            )
            
            page = context.new_page()
            
            # Mask webdriver flag
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            print(f"Navigating to {IXAMBEE_URL}...")
            page.goto(IXAMBEE_URL, wait_until="networkidle", timeout=60000)
            
            # Pause to allow Cloudflare JS challenge to pass if triggered
            page.wait_for_timeout(7000)
            
            # Check if we were caught by Cloudflare
            body_text = page.inner_text("body")
            if "Cloudflare" in body_text or "Verify you are human" in body_text:
                print("Cloudflare challenge page detected. Waiting 5 more seconds...")
                page.wait_for_timeout(5000)
                body_text = page.inner_text("body")

            browser.close()
            return body_text
            
    except Exception as e:
        print(f"Error scraping ixamBee: {e}")
        return ""

def main():
    # 1. Retrieve API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Scrape page text
    raw_text = scrape_ixambee_content()

    if not raw_text or "Cloudflare" in raw_text and "Upcoming Government Exams" not in raw_text:
        print("Scraping blocked or returned no exam data.")
        return

    # 3. Prompt for Groq AI
    prompt = (
        f"Below is raw extracted text from ixamBee's 'Upcoming Government Exams' page:\n\n"
        f"{raw_text[:7000]}\n\n"
        "Instructions:\n"
        "1. Extract ALL upcoming government exams listed in the text.\n"
        "2. Format the response as a clean Telegram message with emojis.\n"
        "3. Categorize them logically (e.g., Banking, Insurance & Regulatory, State/Central Exams).\n"
        "4. For every exam, list:\n"
        "   - 📌 **Exam Name**\n"
        "   - 🗓️ **Form Filling Dates**\n"
        "   - 📅 **Exam Dates (Prelims / Mains)**\n"
        "5. Keep the response concise and ready for mobile broadcast."
    )

    # 4. Call Groq API
    print("Sending extracted data to Groq for parsing...")
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a precise alert agent that extracts exam schedules from website text and formats them for Telegram."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    message_text = completion.choices[0].message.content

    # 5. Send to Telegram
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")

    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text
    }

    print("Sending update to Telegram...")
    response = requests.post(telegram_url, json=payload)
    
    if response.status_code == 200:
        print("Success! Live exam updates sent to Telegram.")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
