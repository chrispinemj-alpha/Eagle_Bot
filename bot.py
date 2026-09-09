from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = "8560176445:AAGVgZCCAPt5odcnACUWJCFEcreWMs54gLo"
YOUR_USER_ID = "6992393855"

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

@app.route('/', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if data and "message" in data:
            msg = data["message"]
            if "text" in msg:
                user = msg["from"]
                user_name = user.get("username", user.get("first_name", "Unknown"))
                user_id = user["id"]
                text = msg["text"]

                forward_text = f"📩 **New Order/Inquiry**\n\n"
                forward_text += f"👤 User: {user_name}\n"
                forward_text += f"🆔 ID: `{user_id}`\n"
                forward_text += f"📝 Message:\n{text}"

                send_telegram_message(YOUR_USER_ID, forward_text)
                send_telegram_message(user_id, "✅ Your message has been received! Our team will get back to you shortly. Thank you for choosing Eagle Web Commerce!")

        return "ok", 200
    except Exception as e:
        print(e)
        return "error", 500

@app.route('/')
def index():
    return "Eagle Web Commerce Bot is running!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
