import telebot
import requests
import time
import threading
from flask import Flask
import os
import re
import random # Rastgele domain seçimi için

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

# --- YENİLENMİŞ DOMAIN SEÇİCİ ---
def get_random_domain():
    """
    Sistemi atlatmak için her seferinde listeden RASTGELE
    bir domain seçer (Sadece en baştakini almaz).
    """
    try:
        res = requests.get(f"{BASE_URL}/domains").json()
        if 'hydra:member' in res:
            # Tüm aktif domainleri listele
            available_domains = [d['domain'] for d in res['hydra:member']]
            # Aralarından rastgele birini seç
            selected = random.choice(available_domains)
            return selected
    except:
        pass
    return "virgillian.com" # Yedek

# --- HESAP OLUŞTURMA ---
def create_new_account(chat_id):
    try:
        # Rastgele domain al
        domain = get_random_domain()
        
        import string
        # İsmi daha gerçekçi yapmak için 10 haneli yapalım
        user_prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        password = "PassWord123!"
        email = f"{user_prefix}@{domain}"

        # Hesap Oluştur
        requests.post(f"{BASE_URL}/accounts", json={"address": email, "password": password})
        
        # Token Al
        token_res = requests.post(f"{BASE_URL}/token", json={"address": email, "password": password}).json()
        
        if 'token' in token_res:
            token = token_res['token']
            if chat_id not in user_data: user_data[chat_id] = {}
            user_data[chat_id]['token'] = token
            user_data[chat_id]['email'] = email
            
            bot.send_message(chat_id, f"✅ *Yeni Hesabın Hazır:* \n\n`{email}` \n\n_Domain: {domain}_", parse_mode='Markdown')
            return True
        else:
            bot.send_message(chat_id, "⚠️ Bu domain dolu çıktı, tekrar deniyorum...")
            create_new_account(chat_id) # Tekrar dene
            return False
    except:
        bot.send_message(chat_id, "❌ Hata oluştu.")
        return False

# --- KOD AYIKLAYICI ---
def extract_verification_code(text):
    # Nubee AI genellikle 6-7 haneli büyük harf/rakam kullanır
    code_pattern = r'\b[A-Z0-9]{6,7}\b'
    match = re.search(code_pattern, text)
    if match: return match.group()
    return None

# --- OTOMATİK KONTROL ---
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
                            subject = full_msg['subject']
                            found_code = extract_verification_code(subject) or extract_verification_code(mail_content)
                            
                            # Bildirim
                            output = (f"📩 *GELEN MAİL*\n"
                                     f"👤 {full_msg['from']['address']}\n"
                                     f"📝 {subject}")
                            bot.send_message(chat_id, output, parse_mode='Markdown')

                            if found_code:
                                # Kodu ver ve hemen YENİ hesaba geç
                                bot.send_message(chat_id, f"🔑 *Kodun:* `{found_code}`", parse_mode='Markdown')
                                time.sleep(2)
                                bot.send_message(chat_id, "🔄 Yeni domain ile hesap açılıyor...")
                                create_new_account(chat_id)
                            
                            requests.delete(f"{BASE_URL}/messages/{msg_id}", headers=headers)
        except: pass
        time.sleep(10)

@bot.message_handler(commands=['yeni'])
def manual_new(message):
    create_new_account(message.chat.id)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 *Anti-Blok Modu Aktif!*\n\nArtık her seferinde farklı domainler deneyeceğim. /yeni yazarak başla.")

if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=run_web_server).start()
    threading.Thread(target=auto_check, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
