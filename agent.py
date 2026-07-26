import os
import requests
from bs4 import BeautifulSoup
from groq import Groq

# Source URL
TARGET_URL = "https://www.freejobalert.com/"

def extract_jobs_with_links():
    """Fetch raw page HTML and extract both text and direct hyperlink references."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove navigation, scripts, and footers
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
            
        extracted_items = []
        
        # Extract text alongside links
        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(strip=True)
            href = a_tag["href"].strip()
            
            # Filter for relevant job entries
            if len(text) > 8 and href.startswith("http"):
                extracted_items.append(f"Title: {text} | Link: {href}")
                
        return "\n".join(extracted_items[:150])  # Send relevant slice
        
    except Exception as e:
        print(f"Error fetching page data: {e}")
        return ""

def main():
    # 1. Retrieve Groq API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Extract Data & Links
    print("Fetching live exam updates and links...")
    raw_payload = extract_jobs_with_links()

    if not raw_payload:
        print("No job data could be retrieved.")
        return

    # 3. LLM Prompt with strict link preservation instructions
    system_instruction = (
        "You are an automated government exam alert assistant. "
        "Your job is to parse raw recruitment items, format them into clean Telegram notifications, "
        "and attach their respective direct links.\n"
        "STRICT RULE: NEVER mention brand names, academy names, or third-party platform names."
    )

    user_prompt = (
        f"Below is raw extracted job data containing exam titles and links:\n\n"
        f"--- RAW DATA START ---\n"
        f"{raw_payload}\n"
        f"--- RAW DATA END ---\n\n"
        "Instructions:\n"
        "1. Identify active or upcoming government exam notifications from the raw list.\n"
        "2. Group them into clear categories (e.g., 🏦 Banking & Finance, 🏛️ Regulatory & Defense, 📑 State Level, 🚆 Railways & SSC).\n"
        "3. For EVERY notification item, present:\n"
        "   - 📌 **Exam / Recruitment Name**\n"
        "   - 🗓️ **Application Window / Status** (e.g., 'Apply Online', 'Closing Soon')\n"
        "   - 📊 **Vacancies / Details** (if mentioned in title)\n"
        "   - 🔗 **Direct Link**: [Apply / Details Here](URL_FOUND_IN_DATA)\n"
        "4. DO NOT mention any source website names or third-party brands in the output.\n"
        "5. Format nicely with Telegram Markdown."
    )

    print("Generating update with links via Groq...")
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
        "parse_mode": "Markdown",
        "disable_web_page_preview": True  # Keeps Telegram messages compact without large link previews
    }

    print("Sending update to Telegram...")
    response = requests.post(telegram_url, json=payload)
    
    if response.status_code == 200:
        print("Success! Notification update with links sent to Telegram.")
    else:
        # Fallback if Telegram Markdown parsing hits unexpected characters
        payload.pop("parse_mode")
        requests.post(telegram_url, json=payload)
        print("Sent plain-text fallback update to Telegram.")

if __name__ == "__main__":
    main()
