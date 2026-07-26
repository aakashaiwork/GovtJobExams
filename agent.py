import os
import requests
from bs4 import BeautifulSoup
from groq import Groq
from playwright.sync_api import sync_playwright

IXAMBEE_URL = "https://www.ixambee.com/upcoming-government-exams"

def scrape_ixambee_table():
    """Scrape the main 'Upcoming Government Exams' table using headless Playwright browser."""
    try:
        with sync_playwright() as p:
            # Launch headless Chromium with standard browser arguments
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()
            
            # Navigate to URL and wait until DOM is loaded
            print(f"Navigating to {IXAMBEE_URL} via Playwright...")
            page.goto(IXAMBEE_URL, wait_until="domcontentloaded", timeout=30000)
            
            # Allow a short delay for any dynamic content/tables to render
            page.wait_for_timeout(3000)
            
            html_content = page.content()
            browser.close()

        soup = BeautifulSoup(html_content, "html.parser")
        tables = soup.find_all("table")
        
        if not tables:
            return "Could not find exam tables on the webpage."

        extracted_data = []
        for table in tables:
            rows = table.find_all("tr")
            for row in rows[1:]:  # Skip header row
                cols = [col.text.strip() for col in row.find_all(["td", "th"])]
                if len(cols) >= 3:
                    exam_name = " ".join(cols[0].split())
                    form_dates = " ".join(cols[1].split())
                    exam_dates = " ".join(cols[2].split())
                    
                    if exam_name:
                        extracted_data.append(
                            f"Exam: {exam_name}\nApplication Window: {form_dates}\nExam Date: {exam_dates}\n"
                        )
                        
        return "\n".join(extracted_data)
        
    except Exception as e:
        print(f"Error scraping ixamBee with Playwright: {e}")
        return ""

def main():
    # 1. Retrieve API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Scrape exact ixamBee page
    scraped_data = scrape_ixambee_table()

    if not scraped_data:
        print("Scraping returned no data.")
        return

    # 3. Dynamic Prompt for Groq
    prompt = (
        f"Below is raw table data extracted directly from ixamBee's 'Upcoming Government Exams' page:\n\n"
        f"{scraped_data}\n\n"
        "Instructions:\n"
        "1. Create a full, clean Telegram notification summarizing ALL exams listed above.\n"
        "2. Group/Organize them logically into categories (e.g., Banking & Financial, Insurance & Regulatory, Central/Railways/SSC, State Level, etc.).\n"
        "3. For every exam, present:\n"
        "   - 📌 **Exam Name**\n"
        "   - 🗓️ **Form Filling Dates**\n"
        "   - 📅 **Exam Dates (Prelims/Mains)**\n"
        "4. Keep the formatting clean and easy to read on mobile."
    )

    # 4. Call Groq API
    print("Sending scraped data to Groq for formatting...")
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a precise educational alert bot providing government exam updates scraped directly from ixamBee."
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
        print("Success! Live ixamBee updates sent to Telegram.")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
