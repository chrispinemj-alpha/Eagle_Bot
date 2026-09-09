import requests
from flask import Flask, request

app = Flask(name)

====== EDIT THESE TWO LINES ======
BOT_TOKEN = "8560176445:AAGVgZCCAPt5odcnACUWJCFEcreWMs54gLo
" # From @BotFather on Telegram
YOUR_USER_ID = "6992393855" # From @userinfobot on Telegram
==================================

def send_telegram_message(chat_id, text):
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
requests.post(url, json=payload)

@app.route('/', methods=['POST'])
def webhook():
try:
data = request.get_json()
if data and 'message' in data:
msg = data['message']
if 'text' in msg:
user = msg['from']
username = user.get('username', user.get('first_name', 'Unknown'))
user_id = user['id']
text = msg['text']

forward_text = f"📩 New Order/Inquiry\n\n"
forward_text += f"👤 User: {username}\n"
forward_text += f"🆔 ID: {user_id}\n"
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

if name == "main":
app.run()
