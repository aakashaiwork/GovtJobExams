import os
import requests
from bs4 import BeautifulSoup
from groq import Groq
from playwright.sync_api import sync_playwright

IXAMBEE_URL = "https://www.ixambee.com/upcoming-government-exams"

def scrape_ixambee_table():
    """Scrape the main 'Upcoming Government Exams' page using Playwright."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()
            
            print(f"Navigating to {IXAMBEE_URL}...")
            page.goto(IXAMBEE_URL, wait_until="networkidle", timeout=45000)
            
            # Wait explicitly for table elements to appear
            try:
                page.wait_for_selector("table", timeout=10000)
            except Exception:
                print("Table selector timeout, attempting full text capture...")
            
            html_content = page.content()
            browser.close()

        soup = BeautifulSoup(html_content, "html.parser")
        tables = soup.find_all("table")
        
        extracted_data = []

        if tables:
            for table in tables:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header row
                    cols = [col.text.strip() for col in row.find_all(["td", "th"])]
                    if len(cols) >= 3:
                        exam_name = " ".join(cols[0].split())
                        form_dates = " ".join(cols[1].split())
                        exam_dates = " ".join(cols[2].split())
                        
                        if exam_name and len(exam_name) > 2:
                            extracted_data.append(
                                f"Exam: {exam_name} | Application Window: {form_dates} | Exam Date: {exam_dates}"
                            )
        
        # Fallback: Extract text content directly if tables structured via divs/cards
        if not extracted_data:
            print("Parsing text nodes as fallback...")
            lines = [line.strip() for line in soup.get_text().split("\n") if line.strip()]
            # Capture relevant chunk
            filtered_lines = []
            capture = False
            for line in lines:
                if "Upcoming Government Exams" in line:
                    capture = True
                if capture:
                    filtered_lines.append(line)
                if len(filtered_lines) > 200:
                    break
            return "\n".join(filtered_lines)

        return "\n".join(extracted_data)
        
    except Exception as e:
        print(f"Error scraping ixamBee: {e}")
        return ""

def main():
    # 1. Retrieve API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Scrape page
    scraped_data = scrape_ixambee_table()

    if not scraped_data:
        print("Scraping returned no data.")
        return

    # 3. Dynamic Prompt for Groq
    prompt = (
        f"Below is live extracted data from ixamBee's 'Upcoming Government Exams' page:\n\n"
        f"{scraped_data[:6000]}\n\n"
        "Instructions:\n"
        "1. Parse the extracted data above and build a complete, cleanly structured Telegram update.\n"
        "2. List ALL upcoming government exams found in the data.\n"
        "3. For every exam, clearly highlight:\n"
        "   - 📌 **Exam Name**\n"
        "   - 🗓️ **Form Filling / Application Window**\n"
        "   - 📅 **Exam Dates (Prelims / Mains)**\n"
        "4. Organize into logical categories (e.g., Banking, Insurance/Regulatory, SSC/Railways, State Level) and format neatly with emojis for Telegram."
    )

    # 4. Call Groq API
    print("Sending extracted page data to Groq...")
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a precise educational alert bot providing government exam updates extracted from ixamBee."
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
        print("Success! Live exam list sent to Telegram.")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
