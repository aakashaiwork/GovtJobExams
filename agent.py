import os
import requests
from bs4 import BeautifulSoup
from groq import Groq

# Target URL
TARGET_URL = "https://www.freejobalert.com/"

def get_clean_page_text():
    """Fetch raw page text and strip site structural tags to get unbranded exam updates."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Strip scripts, styles, header, footer, and navigation
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
            
        raw_lines = soup.get_text(separator="\n").split("\n")
        cleaned_lines = [line.strip() for line in raw_lines if line.strip()]
        
        return "\n".join(cleaned_lines)
        
    except Exception as e:
        print(f"Error fetching page data: {e}")
        return ""

def main():
    # 1. Retrieve Groq API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Extract Web Content
    print(f"Fetching live updates...")
    page_text = get_clean_page_text()

    if not page_text:
        print("No content could be retrieved.")
        return

    # Payload slice
    content_payload = page_text[:8000]

    # 3. Dedicated Prompt enforcing strict anonymity rules
    system_instruction = (
        "You are an automated, completely unbranded educational alert assistant. "
        "Your task is to extract official government exam updates and format them as clean Telegram messages. "
        "STRICT RULE: NEVER mention any third-party websites, source brand names, edtech platforms, or external URLs."
    )

    user_prompt = (
        f"Below is raw extracted text containing recent recruitment updates:\n\n"
        f"--- RAW TEXT START ---\n"
        f"{content_payload}\n"
        f"--- RAW TEXT END ---\n\n"
        "Instructions:\n"
        "1. Identify active or upcoming government exam notifications from the raw text.\n"
        "2. Group them logically into categories (e.g., 🏦 Banking & Finance, 🏛️ Regulatory & Defense, 📑 State Level, 🚆 Railways & SSC).\n"
        "3. For EVERY notification, present:\n"
        "   - 📌 **Exam / Recruitment Name**\n"
        "   - 🗓️ **Application Window / Important Dates**\n"
        "   - 📊 **Vacancies / Details** (if present)\n"
        "4. DO NOT mention any source website names, academy names, edtech brands, or include external web links in your output.\n"
        "5. Keep the response formatted cleanly with Telegram Markdown."
    )

    print("Processing updates via Groq...")
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    message_text = completion.choices[0].message.content

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
        print("Success! Unbranded update sent to Telegram.")
    else:
        # Fallback without Markdown
        payload.pop("parse_mode")
        requests.post(telegram_url, json=payload)
        print("Sent plain-text fallback update to Telegram.")

if __name__ == "__main__":
    main()
