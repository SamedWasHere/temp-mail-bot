import telebot
import requests
import time
import threading
from flask import Flask
import os

# --- AYARLAR ---
API_TOKEN = '8439073268:AAEfIABXx7bAU4qd0lcEEbFes3OoYUvtf2M'
bot = telebot.TeleBot(API_TOKEN)
BASE_URL = "https://api.mail.tm"

user_accounts = {} # {chat_id: {'email': '...', 'token': '...', 'id': '...'}}

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Aktif!"

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- MAİL FONKSİYONLARI ---
def get_domain():
    res = requests.get(f"{BASE_URL}/domains").json()
    return res['hydra:member'][0]['domain']

def auto_check():
    while True:
        try:
            for chat_id, data in list(user_accounts.items()):
                headers = {"Authorization": f"Bearer {data['token']}"}
                # Mesajları kontrol et
                msgs = requests.get(f"{BASE_URL}/messages", headers=headers).json()
                
                if msgs['hydra:member']:
                    for msg in msgs['hydra:member']:
                        msg_id = msg['id']
                        # Daha önce okunmamışsa içeriği çek
                        full_msg = requests.get(f"{BASE_URL}/messages/{msg_id}", headers=headers).json()
                        
                        output = (f"📩 *YENİ MAİL!*\n\n"
                                 f"👤 *Kimden:* {full_msg['from']['address']}\n"
                                 f"📌 *Konu:* {full_msg['subject']}\n\n"
                                 f"📝 *Mesaj:*\n{full_msg['text']}")
                        
                        bot.send_message(chat_id, output, parse_mode='Markdown')
                        # Okunan mesajı sil ki tekrar gelmesin
                        requests.delete(f"{BASE_URL}/messages/{msg_id}", headers=headers)
        except: pass
        time.sleep(15)

@bot.message_handler(commands=['yeni'])
def new_mail(message):
    try:
        domain = get_domain()
        import random, string
        user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        password = "PassWord123!"
        email = f"{user}@{domain}"

        # Hesap Oluştur
        requests.post(f"{BASE_URL}/accounts", json={"address": email, "password": password})
        
        # Token Al (Giriş Yap)
        token_res = requests.post(f"{BASE_URL}/token", json={"address": email, "password": password}).json()
        token = token_res['token']
        
        user_accounts[message.chat.id] = {'email': email, 'token': token}
        bot.reply_to(message, f"✅ *Yeni Mailin:* \n\n`{email}` \n\n_👆 Üzerine dokunarak kopyalayabilirsin._", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "❌ Yeni mail oluşturulamadı. Lütfen tekrar dene.")

if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=run_web_server).start()
    threading.Thread(target=auto_check, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
