import os
import requests
from groq import Groq
from ddgs import DDGS

def get_live_exam_news():
    """Fetch active government job openings, registration windows, and exam schedules."""
    queries = [
        "ixambee upcoming government exams 2026 application dates exam dates",
        "OJAS Gujarat upcoming government exam recruitment application dates 2026",
        "GPSC GSSSB recruitment notification active registration dates 2026",
        "UPSC SSC IBPS notification application deadline exam schedule 2026"
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
                    news_snippets.append(f"Title: {title}\nDetails: {snippet}\nURL: {url}\n")
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
    print("Fetching active recruitment timelines from the web...")
    live_context = get_live_exam_news()

    # 3. Dynamic Prompt Requiring Exact Structured Data
    prompt = (
        f"Here are live search snippets regarding active government exam notifications:\n\n"
        f"{live_context}\n\n"
        "Instructions:\n"
        "Generate a structured, highly detailed notification alert covering ALL active and upcoming government exams for Central (UPSC, SSC, IBPS, Railways, Banks) and Gujarat State (GPSC, GSSSB, OJAS, PSI/ASI).\n\n"
        "For EACH exam listed, you MUST explicitly provide the following 4 structured details:\n"
        "1. 📌 **Exam / Organization Name**\n"
        "2. 🗓️ **Application Window (Start Date - End Date)**\n"
        "3. 📅 **Exam Date (Prelims / Mains / Single Stage)**\n"
        "4. 🔗 **Official Portal Link / Reference**\n\n"
        "Format the message cleanly using clear bullet points and emoji headers so it looks professional on mobile.\n"
        "Do NOT write generic summaries. Only output concrete exam titles, dates, and deadlines."
    )

    # 4. Call Groq API
    print("Generating structured response via Groq...")
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a precise educational alert bot providing structured government exam timelines and dates."
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
        "text": message_text,
        "parse_mode": "Markdown"
    }

    print("Sending structured update to Telegram...")
    response = requests.post(telegram_url, json=payload)
    
    if response.status_code == 200:
        print("Success! Structured exam updates sent to Telegram.")
    else:
        # Fallback if markdown parsing fails due to special characters
        payload.pop("parse_mode", None)
        requests.post(telegram_url, json=payload)
        print("Success! Sent without parse_mode formatting.")

if __name__ == "__main__":
    main()
