import os
import requests
from google import genai

# --- CONFIGURATION FROM GITHUB SECRETS ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

def fetch_exam_notifications():
    """
    Fetches raw notification data.
    """
    # Placeholder sample data
    raw_data = """
    1. GSSSB Supervisor Recruitment 2026: Released for 436 vacancies. Application start date: July 20. Last date: Aug 3. Qualification: Diploma/Degree. Link: https://gsssb.gujarat.gov.in
    2. SSC CGL Tier 1 Exam Date update released on ssc.gov.in. Admit card expected next week.
    3. GPSC Prelims answer key released for Advt No 45/2026. Objections open till July 30.
    """
    return raw_data

def summarize_with_gemini(raw_text):
    """Passes raw notification data to Gemini for structured formatting."""
    prompt = f"""
    You are a daily Exam Alert Assistant for Central and Gujarat State Government exams.
    Summarize the following exam updates into a clean, easy-to-read Telegram message.

    Formatting rules:
    - Group into: 🏛️ Gujarat Govt (OJAS/GPSC/GSSSB) and 🇮🇳 Central Govt (UPSC/SSC/IBPS).
    - Use bullet points with Bold headings.
    - Include Post Name, Vacancies (if any), Last Date (if any), and Official Link.
    - Keep it crisp and direct.

    Raw Updates:
    {raw_text}
    """

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )
    return response.text

def send_telegram_message(message_text):
    """Sends the formatted summary to your Telegram chat/channel."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown",
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Message successfully sent to Telegram!")
    else:
        print(f"❌ Failed to send message: {response.text}")

if __name__ == "__main__":
    print("Fetching exam updates...")
    raw_updates = fetch_exam_notifications()

    print("Generating AI Summary...")
    ai_summary = summarize_with_gemini(raw_updates)

    print("\n--- AI Generated Daily Brief ---")
    print(ai_summary)

    send_telegram_message(ai_summary)
