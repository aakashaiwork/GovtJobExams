import os
import requests
from bs4 import BeautifulSoup
from groq import Groq
from playwright.sync_api import sync_playwright

IXAMBEE_URL = "https://www.ixambee.com/upcoming-government-exams"

def scrape_ixambee_content():
    """Scrape ixamBee page using Playwright with deep scrolling to trigger JS lazy-loads."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()
            
            print(f"Navigating to {IXAMBEE_URL}...")
            page.goto(IXAMBEE_URL, wait_until="domcontentloaded", timeout=60000)
            
            # Wait 5 seconds for initial JS rendering
            page.wait_for_timeout(5000)
            
            # Scroll down to trigger lazy loading of exam tables
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
            page.wait_for_timeout(2000)
            
            # Get full inner text of the page body
            body_text = page.inner_text("body")
            browser.close()

            return body_text
            
    except Exception as e:
        print(f"Error scraping ixamBee with Playwright: {e}")
        return ""

def main():
    # 1. Retrieve API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Scrape page text
    raw_text = scrape_ixambee_content()

    if not raw_text or len(raw_text.strip()) < 100:
        print("Scraping returned no meaningful data.")
        return

    # Clean text to avoid token limits while preserving table content
    cleaned_lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    condensed_text = "\n".join(cleaned_lines[:400])  # Take primary content block

    print(f"Successfully extracted {len(condensed_text)} characters from page.")

    # 3. Prompt for Groq AI
    prompt = (
        f"Below is raw extracted text from ixamBee's 'Upcoming Government Exams' page:\n\n"
        f"{condensed_text}\n\n"
        "Instructions:\n"
        "1. Extract ALL upcoming government exams listed in the text.\n"
        "2. Format the response as a clean Telegram message.\n"
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
                "content": "You are a precise alert agent that extracts exam schedules from raw website text and formats them for Telegram."
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
