import os
import requests
from groq import Groq
from ddgs import DDGS

def get_live_exam_news():
    """Fetch live government exam updates from web search."""
    search_query = "Gujarat OJAS GPSC GSSSB recruitment notification 2026 UPSC SSC job alert"
    
    news_snippets = []
    try:
        with DDGS() as ddgs:
            # Get latest text results
            results = list(ddgs.text(search_query, max_results=5))
            for idx, item in enumerate(results, 1):
                title = item.get('title', '')
                snippet = item.get('body', '')
                url = item.get('href', '')
                news_snippets.append(f"{idx}. Title: {title}\nSummary: {snippet}\nURL: {url}\n")
    except Exception as e:
        print(f"Web Search Error: {e}")
        
    return "\n".join(news_snippets)

def main():
    # 1. Retrieve API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Fetch Live Web Search Results
    print("Fetching live exam updates from the web...")
    live_context = get_live_exam_news()

    if not live_context:
        live_context = "No direct web search snippets retrieved. Provide key active recruitment links for GPSC, OJAS, and Central exams."

    # 3. Build Prompt with Real-Time Web Context
    prompt = (
        f"Here are live search results regarding active government exam notifications:\n\n"
        f"{live_context}\n\n"
        "Instructions:\n"
        "1. Summarize current and active government job notifications for Gujarat (GPSC, OJAS, GSSSB) and Central (UPSC, SSC, IBPS).\n"
        "2. Organize clearly using headings and bullet points.\n"
        "3. Only mention active, current notifications. Do not use or mention outdated years like 2024 or 2025."
    )

    # 4. Request Summary from Groq API
    print("Generating response via Groq Llama model...")
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a daily exam alert assistant providing up-to-date Indian government job notifications."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    message_text = completion.choices[0].message.content

    # 5. Telegram API Delivery
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")

    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text
    }

    print("Sending live update to Telegram...")
    response = requests.post(telegram_url, json=payload)
    
    if response.status_code == 200:
        print("Success! Live exam updates sent to Telegram.")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
