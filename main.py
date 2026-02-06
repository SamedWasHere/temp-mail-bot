import telebot
import requests
import time
import threading
from flask import Flask
import os
import re

# --- AYARLAR ---
API_TOKEN = '8439073268:AAEfIABXx7bAU4qd0lcEEbFes3OoYUvtf2M'
bot = telebot.TeleBot(API_TOKEN)
BASE_URL = "https://api.mail.tm"

user_data = {} 

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Aktif!"

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- YENİ MAİL OLUŞTURMA FONKSİYONU (ORTAK) ---
def create_new_account(chat_id):
    """Hem komutla hem de otomatik olarak yeni mail oluşturur."""
    try:
        # Domain al
        dom_res = requests.get(f"{BASE_URL}/domains").json()
        domain = dom_res['hydra:member'][0]['domain']
        
        import random, string
        user_prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        password = "PassWord123!"
        email = f"{user_prefix}@{domain}"

        # Hesap Oluştur
        requests.post(f"{BASE_URL}/accounts", json={"address": email, "password": password})
        
        # Giriş Yap ve Token Al
        token_res = requests.post(f"{BASE_URL}/token", json={"address": email, "password": password}).json()
        token = token_res['token']
        
        # Kullanıcı verisini güncelle
        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]['token'] = token
        user_data[chat_id]['email'] = email
        
        bot.send_message(chat_id, f"✅ *Yeni Mailin Hazırlandı (Otomatik):* \n\n`{email}` \n\n_👆 Kopyalamak için üzerine dokun!_", parse_mode='Markdown')
        return True
    except:
        bot.send_message(chat_id, "❌ Yeni mail otomatik oluşturulurken hata oluştu.")
        return False

def extract_verification_code(text):
    """Metin içindeki 6-7 haneli büyük harf/rakam kodlarını bulur."""
    code_pattern = r'\b[A-Z0-9]{6,7}\b'
    match = re.search(code_pattern, text)
    if match:
        return match.group()
    return None

# --- MAİL KONTROL DÖNGÜSÜ ---
def auto_check():
    while True:
        try:
            for chat_id, data in list(user_data.items()):
                if 'token' in data:
                    headers = {"Authorization": f"Bearer {data['token']}"}
                    msgs = requests.get(f"{BASE_URL}/messages", headers=headers).json()
                    
                    if msgs['hydra:member']:
                        for msg in msgs['hydra:member']:
                            msg_id = msg['id']
                            full_msg = requests.get(f"{BASE_URL}/messages/{msg_id}", headers=headers).json()
                            
                            mail_content = full_msg['text']
                            found_code = extract_verification_code(full_msg['subject']) or extract_verification_code(mail_content)
                            
                            # Maili gönder
                            output = (f"📩 *YENİ MAİL!*\n\n"
                                     f"👤 *Kimden:* {full_msg['from']['address']}\n"
                                     f"📌 *Konu:* {full_msg['subject']}\n\n"
                                     f"📝 *Mesaj:*\n{mail_content}")
                            bot.send_message(chat_id, output, parse_mode='Markdown')

                            if found_code:
                                # 1. Kopyalanabilir kodu gönder
                                bot.send_message(chat_id, f"🔑 *Onay Kodun:* \n\n`{found_code}`", parse_mode='Markdown')
                                
                                # 2. OTOMATİK YENİLEME: Kodu gönderdikten 2 saniye sonra yeni mail ver
                                time.sleep(2)
                                bot.send_message(chat_id, "🔄 Kod alındı, senin için yeni bir mail adresi hazırlıyorum...")
                                create_new_account(chat_id)
                            
                            requests.delete(f"{BASE_URL}/messages/{msg_id}", headers=headers)
        except: pass
        time.sleep(15)

@bot.message_handler(commands=['yeni'])
def manual_new_mail(message):
    create_new_account(message.chat.id)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🤖 *Tam Otomatik Bot Hazır!*\n\n1. /yeni ile ilk mailini al.\n2. Kod gelince ben kodu ayıklayıp sana vereceğim.\n3. Ardından hemen yeni bir mail adresi oluşturacağım!", parse_mode='Markdown')

if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=run_web_server).start()
    threading.Thread(target=auto_check, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
