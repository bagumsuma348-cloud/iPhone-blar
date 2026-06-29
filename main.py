import telebot
from telebot import types
from PIL import Image, ImageFilter
from rembg import remove
import io
import os
import logging
from flask import Flask, request
import threading

# ========================= CONFIGURATION =========================
BOT_TOKEN = "8599026487:AAF6TtOCpBJnuly-QLnU2sZz3RsdxCP-Bl0"   # ←←← এখানে তোমার টোকেন বসাও

# Branded links (optional)
YOUTUBE_CHANNEL = "https://youtube.com/@yourchannel"
SUPPORT_CHANNEL = "https://t.me/yourchannel"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ========================= FLASK WEBHOOK =========================
@app.route('/')
def index():
    return "✅ Background Blur Bot is LIVE 24/7!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 400

# ========================= BOT COMMANDS =========================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 <b>Welcome to Background Blur Bot!</b>\n\n"
        "📸 যেকোনো ছবি পাঠাও, আমি মানুষ আলাদা করে ব্যাকগ্রাউন্ড ব্লার করে দিব।\n\n"
        "✨ Powered by rembg + PIL\n"
        "Made with ❤️"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🚀 SUBSCRIBE CHANNEL", url=YOUTUBE_CHANNEL))
    markup.add(types.InlineKeyboardButton("📢 SUPPORT CHANNEL", url=SUPPORT_CHANNEL))

    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(content_types=['photo'])
def blur_background(message):
    status_msg = bot.reply_to(message, "⏳ Processing image... Please wait.")

    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        img_bytes = bot.download_file(file_info.file_path)

        bot.edit_message_text(
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            text="🔄 Removing background..."
        )

        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

        # Background removal
        subject = remove(img)

        # Background blur
        bg = img.convert("RGB").filter(ImageFilter.GaussianBlur(25)).convert("RGBA")

        # Paste subject on blurred background
        bg.paste(subject, (0, 0), subject)

        bot.edit_message_text(
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            text="📤 Uploading processed image..."
        )

        output = io.BytesIO()
        bg.convert("RGB").save(output, format="JPEG", quality=95)
        output.seek(0)

        bot.send_photo(
            message.chat.id,
            output,
            caption="✅ Background Blurred Successfully!\n\n🔥 Powered by @yourusername"
        )

        bot.edit_message_text(
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            text="✅ Done!"
        )

    except Exception as e:
        logger.error(str(e))
        try:
            bot.edit_message_text(
                chat_id=status_msg.chat.id,
                message_id=status_msg.message_id,
                text=f"❌ Error: {str(e)[:200]}"
            )
        except:
            pass

# ========================= START FLASK + WEBHOOK =========================
if __name__ == "__main__":
    # Auto set webhook for Render
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if hostname:
        webhook_url = f"https://{hostname}/{BOT_TOKEN}"
        try:
            bot.set_webhook(url=webhook_url)
            logger.info(f"✅ Webhook set: {webhook_url}")
        except Exception as e:
            logger.error(f"Webhook failed: {e}")

    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
