import os
import re
import requests
from bs4 import BeautifulSoup
from groq import Groq

# Main target URL
TARGET_URL = "https://www.freejobalert.com/"

def get_official_apply_link(detail_url):
    """
    Scrapes the individual job page to find official application/notification links
    (e.g., .gov.in, .nic.in, .in, official portal registration URLs).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(detail_url, headers=headers, timeout=10)
        if res.status_code != 200:
            return detail_url
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Look for official apply or notification links in table/anchor tags
        for a_tag in soup.find_all("a", href=True):
            link_text = a_tag.get_text(strip=True).lower()
            href = a_tag["href"].strip()
            
            # Match keywords like "apply online", "official website", "registration"
            if any(k in link_text for k in ["apply online", "registration", "official website", "notification"]):
                # Filter out third-party/internal links
                if href.startswith("http") and not any(domain in href for domain in ["freejobalert", "facebook", "telegram", "whatsapp", "twitter"]):
                    return href
                    
        return None
    except Exception:
        return None

def extract_jobs_and_direct_links():
    """Fetch recent exam updates and resolve their direct official links."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Clean up header/footer elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
            
        extracted_items = []
        count = 0
        
        # Extract job titles and resolve their actual official link
        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(strip=True)
            href = a_tag["href"].strip()
            
            if len(text) > 10 and "freejobalert.com" in href and count < 15:
                # Try resolving the direct official link inside detail page
                official_link = get_official_apply_link(href)
                
                if official_link:
                    extracted_items.append(f"Title: {text} | Official Link: {official_link}")
                    count += 1
                
        return "\n".join(extracted_items)
        
    except Exception as e:
        print(f"Error extracting data: {e}")
        return ""

def sanitize_unbranded_text(text):
    """Safety filter: Removes any accidental mention of third-party websites or brand names."""
    forbidden_words = [
        r"freejobalert\.com", r"freejobalert", r"free job alert", 
        r"testbook", r"ixambee", r"byjus", r"unacademy"
    ]
    cleaned = text
    for pattern in forbidden_words:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned

def main():
    # 1. Retrieve Groq API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Scrape live exam updates & extract official links
    print("Fetching recruitment updates and extracting direct official links...")
    raw_payload = extract_jobs_and_direct_links()

    if not raw_payload:
        print("No job updates found.")
        return

    # 3. LLM Prompt with strict unbranding instructions
    system_instruction = (
        "You are an automated government exam alert assistant. "
        "Your job is to format extracted recruitment updates into clean Telegram alerts with their direct official application links.\n"
        "STRICT RULES:\n"
        "1. DO NOT mention any third-party websites, source brand names, edtech platforms, or intermediary portals.\n"
        "2. ONLY output official portal links provided in the raw data."
    )

    user_prompt = (
        f"Below is raw extracted job data containing exam titles and direct official portal links:\n\n"
        f"--- RAW DATA START ---\n"
        f"{raw_payload}\n"
        f"--- RAW DATA END ---\n\n"
        "Instructions:\n"
        "1. Organize the exams into clear categories (e.g., 🏦 Banking & Finance, 🏛️ Regulatory & Defense, 📑 State Level, 🚆 Railways & SSC).\n"
        "2. For EVERY notification item, present:\n"
        "   - 📌 **Exam / Recruitment Name**\n"
        "   - 🗓️ **Application Window / Status**\n"
        "   - 📊 **Vacancies / Details** (if present in title)\n"
        "   - 🔗 **Direct Apply Link**: [Apply / Official Notification](OFFICIAL_LINK_URL)\n"
        "3. Format cleanly using Telegram Markdown."
    )

    print("Generating unbranded update via Groq...")
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    message_text = completion.choices[0].message.content
    
    # Extra safety pass to strip any branding leftovers
    message_text = sanitize_unbranded_text(message_text)

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
        "disable_web_page_preview": True
    }

    print("Sending update to Telegram...")
    response = requests.post(telegram_url, json=payload)
    
    if response.status_code == 200:
        print("Success! Official link updates sent to Telegram.")
    else:
        # Fallback if Telegram Markdown formatting hits syntax issues
        payload.pop("parse_mode")
        requests.post(telegram_url, json=payload)
        print("Sent plain-text fallback update to Telegram.")

if __name__ == "__main__":
    main()
