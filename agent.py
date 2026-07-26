import os
import requests
from bs4 import BeautifulSoup
from groq import Groq

IXAMBEE_URL = "https://www.ixambee.com/upcoming-government-exams"

def scrape_ixambee_table():
    """Scrape the main 'Upcoming Government Exams' table directly from ixamBee."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(IXAMBEE_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")
        
        if not tables:
            return "Could not find exam tables on the webpage."

        extracted_data = []
        for table in tables:
            rows = table.find_all("tr")
            for row in rows[1:]:  # Skip header row
                cols = [col.text.strip() for col in row.find_all(["td", "th"])]
                if len(cols) >= 3:
                    exam_name = cols[0]
                    form_dates = cols[1]
                    exam_dates = cols[2]
                    
                    # Clean up internal whitespace/newlines
                    exam_name = " ".join(exam_name.split())
                    form_dates = " ".join(form_dates.split())
                    exam_dates = " ".join(exam_dates.split())
                    
                    if exam_name:
                        extracted_data.append(
                            f"Exam: {exam_name}\nApplication Window: {form_dates}\nExam Date: {exam_dates}\n"
                        )
                        
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

    # 2. Scrape exact ixamBee page
    print(f"Scraping {IXAMBEE_URL}...")
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
        "2. Group/Organize them logically into categories (e.g., Banking & Financial, Insurance & Regulatory, Central/Railways/SSC, etc.).\n"
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
