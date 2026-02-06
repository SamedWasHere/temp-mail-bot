import telebot
import requests
import time
import threading
from flask import Flask
import os
import re # Kod yakalamak için gerekli kütüphane

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

# --- AKILLI KOD YAKALAYICI FONKSİYONU ---
def extract_verification_code(text):
    """
    Metin içindeki 6 veya 7 haneli, tamamı büyük harf ve rakamdan 
    oluşan doğrulama kodlarını bulur.
    """
    # Regex: Kelime sınırları içinde, 6-7 karakterlik Büyük Harf ve Rakamlar
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
                            from_addr = full_msg['from']['address']
                            subject = full_msg['subject']
                            
                            # Kodu Yakalamaya Çalış (Hem konudan hem içerikten bak)
                            found_code = extract_verification_code(subject) or extract_verification_code(mail_content)
                            
                            # Standart mail bildirimi
                            output = (f"📩 *YENİ MAİL!*\n\n"
                                     f"👤 *Kimden:* {from_addr}\n"
                                     f"📌 *Konu:* {subject}\n\n"
                                     f"📝 *Mesaj:*\n{mail_content}")
                            
                            bot.send_message(chat_id, output, parse_mode='Markdown')

                            # EĞER KOD BULUNURSA: Ekstra kopyalanabilir mesaj at
                            if found_code:
                                bot.send_message(chat_id, f"🔑 *Nubee AI Onay Kodun:*\n\n`{found_code}`\n\n_👆 Kopyalamak için koda dokun!_", parse_mode='Markdown')
                            
                            # Okunan mesajı sil
                            requests.delete(f"{BASE_URL}/messages/{msg_id}", headers=headers)
        except: pass
        time.sleep(15)

@bot.message_handler(commands=['yeni'])
def new_mail(message):
    try:
        # Domain al
        dom_res = requests.get(f"{BASE_URL}/domains").json()
        domain = dom_res['hydra:member'][0]['domain']
        
        import random, string
        user_prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        password = "PassWord123!"
        email = f"{user_prefix}@{domain}"

        requests.post(f"{BASE_URL}/accounts", json={"address": email, "password": password})
        token_res = requests.post(f"{BASE_URL}/token", json={"address": email, "password": password}).json()
        token = token_res['token']
        
        user_data[message.chat.id] = {'email': email, 'token': token}
        bot.reply_to(message, f"✅ *Yeni Mailin:* \n\n`{email}` \n\n_👆 Dokun ve Kopyala!_", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Mail oluşturulamadı.")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🤖 Nubee AI Akıllı Botu Hazır!\n\n📧 /yeni yazarak mail alabilirsin. Onay kodu gelince onu senin için ayıklayacağım.")

if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=run_web_server).start()
    threading.Thread(target=auto_check, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
