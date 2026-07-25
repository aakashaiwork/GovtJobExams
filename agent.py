import os
import requests
from groq import Groq
from duckduckgo_search import DDGS

def get_live_exam_news():
    """Fetch live government exam updates from web search."""
    search_query = "latest Gujarat OJAS GPSC GSSSB recruitment notification 2026 central govt job alert"
    ddgs = DDGS()
    results = list(ddgs.text(search_query, max_results=5))
    
    news_context = ""
    for idx, item in enumerate(results, 1):
        news_context += f"{idx}. Title: {item.get('title')}\nSnippet: {item.get('body')}\n\n"
    return news_context

def main():
    # 1. Retrieve API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Fetch Live Web Search Results
    print("Fetching live exam updates from the web...")
    live_context = get_live_exam_news()

    # 3. Dynamic Prompt with Live Context
    prompt = (
        f"Here are the latest live web search snippets regarding government exam notifications:\n\n"
        f"{live_context}\n\n"
        "Based ONLY on recent active updates, generate a clean, highly relevant summary of "
        "top government job/exam notifications (UPSC, SSC, IBPS, GPSC, OJAS, GSSSB). "
        "Organize with clean headings and bullet points. Do not mention outdated years like 2024."
    )

    # 4. Call Groq API
    print("Sending live context to Groq API...")
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an accurate educational assistant providing current Indian government exam updates."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    message_text = completion.choices[0].message.content

    # 5. Telegram API details
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variable is missing.")

    # 6. Send to Telegram
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text
    }

    print("Sending update to Telegram...")
    response = requests.post(telegram_url, json=payload)
    if response.status_code == 200:
        print("Success! Live update delivered to Telegram.")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
