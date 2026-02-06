import telebot
import requests
import time
import threading
from flask import Flask
import os

# --- YENİ TOKEN ---
API_TOKEN = '8439073268:AAEfIABXx7bAU4qd0lcEEbFes3OoYUvtf2M'
bot = telebot.TeleBot(API_TOKEN)
API_URL = "https://www.1secmail.com/api/v1/"

# SİTEYE KENDİMİZİ WEB TARAYICISI GİBİ TANITMAK İÇİN (Çok Önemli!)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

user_sessions = {}

# --- RENDER İÇİN WEB SUNUCUSU ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Aktif ve Çalışıyor!"

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- BOT FONKSİYONLARI ---
def auto_check():
    """Gelen kutusunu sürekli kontrol eder"""
    while True:
        try:
            for chat_id, data in list(user_sessions.items()):
                mail = data['mail']
                last_id = data['last_id']
                u, d = mail.split("@")
                
                # Headers ekleyerek isteği gönderiyoruz
                res = requests.get(f"{API_URL}?action=getMessages&login={u}&domain={d}", headers=HEADERS, timeout=10)
                
                if res.status_code == 200:
                    try:
                        messages = res.json()
                        if messages and messages[0]['id'] > last_id:
                            msg_id = messages[0]['id']
                            # İçeriği okurken de headers kullanıyoruz
                            content = requests.get(f"{API_URL}?action=readMessage&login={u}&domain={d}&id={msg_id}", headers=HEADERS, timeout=10).json()
                            
                            output = (f"📩 *YENİ MAİL GELDİ!*\n\n"
                                     f"👤 *Gönderen:* {content['from']}\n"
                                     f"📌 *Konu:* {content['subject']}\n\n"
                                     f"📝 *Mesaj:*\n{content['textBody']}")
                            
                            bot.send_message(chat_id, output, parse_mode='Markdown')
                            user_sessions[chat_id]['last_id'] = msg_id
                    except:
                        pass
        except Exception as e:
            print(f"Hata: {e}")
        time.sleep(10)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🚀 Bot Yenilendi! /yeni yazarak hemen mail al.")

@bot.message_handler(commands=['yeni'])
def new_mail(message):
    try:
        # Maskeli istek (Headers ile)
        res = requests.get(f"{API_URL}?action=genAddrs&count=1", headers=HEADERS, timeout=10)
        
        if res.status_code == 200:
            mail_addr = res.json()[0]
            user_sessions[message.chat.id] = {'mail': mail_addr, 'last_id': 0}
            bot.reply_to(message, f"✅ *Yeni Mailin Hazır:*\n\n`{mail_addr}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"⚠️ Site cevap vermedi. Kod: {res.status_code}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Hata: {str(e)}")

# Sunucuyu ve Botu Başlat
threading.Thread(target=run_web_server).start()
bot.infinity_polling()
