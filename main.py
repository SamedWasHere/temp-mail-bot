import telebot
import requests
import time
import threading
from flask import Flask
import os

# --- AYARLAR ---
API_TOKEN = '8439073268:AAFI8D407_VPDgLC726N25kRRPg_Qm2cnMw'
bot = telebot.TeleBot(API_TOKEN)
API_URL = "https://www.1secmail.com/api/v1/"

user_sessions = {}

# Render için basit bir web sunucusu (Port hatası almamak için)
app = Flask('')

@app.route('/')
def home():
    return "Bot aktif ve çalışıyor!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def auto_check():
    while True:
        try:
            for chat_id, data in list(user_sessions.items()):
                mail = data['mail']
                last_id = data['last_id']
                u, d = mail.split("@")
                res = requests.get(f"{API_URL}?action=getMessages&login={u}&domain={d}", timeout=10).json()
                if res and res[0]['id'] > last_id:
                    msg_id = res[0]['id']
                    content = requests.get(f"{API_URL}?action=readMessage&login={u}&domain={d}&id={msg_id}").json()
                    output = (f"📩 *YENİ MAİL!*\n\n*Gönderen:* {content['from']}\n"
                             f"*Konu:* {content['subject']}\n\n*Mesaj:*\n{content['textBody']}")
                    bot.send_message(chat_id, output, parse_mode='Markdown')
                    user_sessions[chat_id]['last_id'] = msg_id
        except: pass
        time.sleep(10)

@bot.message_handler(commands=['yeni'])
def new_mail(message):
    try:
        res = requests.get(f"{API_URL}?action=genAddrs&count=1").json()
        mail_addr = res[0]
        user_sessions[message.chat.id] = {'mail': mail_addr, 'last_id': 0}
        bot.reply_to(message, f"✅ *Yeni Mailin Hazır (Render):*\n\n`{mail_addr}`", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Hata: {str(e)}")

# Thread'leri başlat
threading.Thread(target=auto_check, daemon=True).start()
threading.Thread(target=run_flask).start()

bot.infinity_polling()
