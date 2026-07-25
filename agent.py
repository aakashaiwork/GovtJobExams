import os
import requests
from groq import Groq
from ddgs import DDGS

def get_live_exam_news():
    """Fetch all active openings, notifications, and exam updates for the current month."""
    queries = [
        "OJAS Gujarat recruitment notification July 2026 apply online",
        "GPSC GSSSB latest notification exam schedule July 2026",
        "UPSC SSC IBPS latest exam notification recruitment July 2026"
    ]
    
    news_snippets = []
    try:
        with DDGS() as ddgs:
            for q in queries:
                results = list(ddgs.text(q, max_results=3))
                for item in results:
                    title = item.get('title', '')
                    snippet = item.get('body', '')
                    url = item.get('href', '')
                    news_snippets.append(f"Title: {title}\nSummary: {snippet}\nLink: {url}\n")
    except Exception as e:
        print(f"Web Search Error: {e}")
        
    return "\n".join(news_snippets)

def main():
    # 1. Retrieve API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Fetch Live Search Snippets
    print("Fetching active recruitment updates for current month...")
    live_context = get_live_exam_news()

    if not live_context:
        live_context = "Check OJAS (ojas.gujarat.gov.in) and GPSC (gpsc.gujarat.gov.in) portals directly for active notifications."

    # 3. Dynamic Prompt for Broad Coverage
    prompt = (
        f"Here are live search snippets regarding active government exam notifications:\n\n"
        f"{live_context}\n\n"
        "Instructions:\n"
        "1. Provide a comprehensive summary of ALL active openings, ongoing application deadlines, and exam updates "
        "released or active in the current month (July 2026).\n"
        "2. Focus heavily on Gujarat state exams (GPSC, GSSSB, OJAS, PSI/ASI) as well as major Central notifications (UPSC, SSC, IBPS).\n"
        "3. Organize clearly using headings:\n"
        "   - 🚀 New Openings & Advertisements\n"
        "   - ⏳ Application Deadlines This Month\n"
        "   - 📅 Exam Dates & Hall Ticket Updates\n"
        "4. Include key dates and official links where applicable. Keep the formatting clear and easy to read on mobile."
    )

    # 4. Request Summary from Groq API
    print("Generating update via Groq Llama model...")
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an automated educational alert bot providing full-scope Indian and Gujarat government job updates."
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
        print("Success! Expanded exam updates sent to Telegram.")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
