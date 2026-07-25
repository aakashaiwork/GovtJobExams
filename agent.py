import os
import requests
from groq import Groq

def main():
    # 1. Retrieve API Key and initialize Groq Client
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    groq_client = Groq(api_key=groq_api_key)

    # 2. Prompt for daily exam and recruitment updates
    prompt = (
        "Provide a clean, well-structured, professional daily summary of top government "
        "job/exam notifications in India (UPSC, SSC, IBPS, Railway) and Gujarat state updates "
        "(GPSC, GSSSB, OJAS, PSI/ASI). Group them neatly under headings with bullet points."
    )

    # 3. Call Groq API (using Llama 3.3 70B model)
    print("Fetching response from Groq API...")
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful educational assistant for competitive exam updates."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    message_text = completion.choices[0].message.content
    print("Generated Message Length:", len(message_text))

    # 4. Telegram API details
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variable is missing.")

    # 5. Send message to Telegram
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text
    }

    print("Sending message to Telegram...")
    response = requests.post(telegram_url, json=payload)
    
    if response.status_code == 200:
        print("Success! Message delivered to Telegram.")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
