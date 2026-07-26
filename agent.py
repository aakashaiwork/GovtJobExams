import os
import requests
from bs4 import BeautifulSoup
from groq import Groq

# Target Page URL
IXAMBEE_URL = "https://www.ixambee.com/upcoming-government-exams"

def get_clean_page_text():
    """Fetch raw page HTML and strip out structural tags to get plain text for LLM processing."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(IXAMBEE_URL, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script tags, style tags, and header/footer noise
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
            
        # Get extracted text lines
        raw_lines = soup.get_text(separator="\n").split("\n")
        cleaned_lines = [line.strip() for line in raw_lines if line.strip()]
        
        return "\n".join(cleaned_lines)
        
    except Exception as e:
        print(f"Error fetching web page: {e}")
        return ""

def main():
    # 1. Retrieve Groq API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Extract Web Content
    print(f"Fetching data from {IXAMBEE_URL}...")
    page_text = get_clean_page_text()

    if not page_text:
        print("No text content could be fetched.")
        return

    # Truncate text to keep within token limits while capturing main content
    content_payload = page_text[:8000]

    # 3. Dedicated Prompt for Llama-3.3-70b
    system_instruction = (
        "You are an automated government exam alert assistant. "
        "Your sole task is to process raw web text, extract all exam details, "
        "and format them into a beautiful, highly readable Telegram notification."
    )

    user_prompt = (
        f"Below is raw extracted text from ixamBee's 'Upcoming Government Exams' page:\n\n"
        f"--- RAW TEXT START ---\n"
        f"{content_payload}\n"
        f"--- RAW TEXT END ---\n\n"
        "Instructions:\n"
        "1. Identify all government and banking exams listed in the text.\n"
        "2. If no exam table is found in the text, respond strictly with: 'No active exams found.'\n"
        "3. Otherwise, group the exams into neat categories (e.g., 🏦 Banking & Finance, 🏛️ Regulatory & Defense, 📑 State & Others).\n"
        "4. For EVERY exam, present:\n"
        "   - 📌 **Exam Name**\n"
        "   - 🗓️ **Form Filling Dates**\n"
        "   - 📅 **Exam Dates (Prelims / Mains)**\n"
        "5. Keep the formatting clean, mobile-friendly, and formatted in Markdown for Telegram."
    )

    print("Processing scraped text via Groq LLM prompt...")
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    message_text = completion.choices[0].message.content

    # Skip sending if LLM found no exams or hit a block
    if "No active exams found" in message_text:
        print("LLM found no exam details in the page content.")
        return

    # 4. Dispatch to Telegram
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")

    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "Markdown"
    }

    print("Sending update to Telegram...")
    response = requests.post(telegram_url, json=payload)
    
    if response.status_code == 200:
        print("Success! Clean LLM-formatted update sent to Telegram.")
    else:
        # Retry without Markdown parsing in case of unescaped Telegram syntax
        payload.pop("parse_mode")
        requests.post(telegram_url, json=payload)
        print("Sent fallback plain-text update to Telegram.")

if __name__ == "__main__":
    main()
