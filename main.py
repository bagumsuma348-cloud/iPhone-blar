import telebot
from telebot import types
from PIL import Image, ImageFilter, ImageOps
from rembg import remove
import io
import os
import logging
from flask import Flask, request

# ========================= CONFIGURATION =========================
BOT_TOKEN = "8599026487:AAF6TtOCpBJnuly-QLnU2sZz3RsdxCP-Bl0"   # ←←← তোমার টোকেন বসাও

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ========================= FLASK WEBHOOK =========================
@app.route('/')
def index():
    return "✅ iPhone Style Blur Bot is LIVE 24/7!"

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
        "👋 <b>iPhone Style Background Blur Bot</b>\n\n"
        "📸 যেকোনো ছবি পাঠাও\n"
        "মানুষ sharp রেখে ব্যাকগ্রাউন্ড iPhone এর মতো সুন্দর করে ব্লার করে দিব।\n\n"
        "✨ Natural Blur • Edge Feather\n"
        "Made with ❤️"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/BK444_Official"))

    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(content_types=['photo'])
def iphone_style_blur(message):
    status_msg = bot.reply_to(message, "⏳ iPhone Style Blur করতেছি...")

    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        img_bytes = bot.download_file(file_info.file_path)

        bot.edit_message_text(
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            text="🔄 Background আলাদা করা হচ্ছে..."
        )

        # Open image
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

        # Remove background (keep subject)
        subject = remove(img)

        # Create blurred background (iPhone-like strong blur)
        bg = img.convert("RGB").filter(ImageFilter.GaussianBlur(35))  # Increased blur for iPhone feel

        # Add slight vignette for more natural look
        bg = bg.filter(ImageFilter.GaussianBlur(2))

        # Convert to RGBA
        bg = bg.convert("RGBA")

        # Feather the edges of the subject for smoother blending
        subject = ImageOps.expand(subject, border=5, fill=(0,0,0,0))
        subject = subject.filter(ImageFilter.SMOOTH)

        # Paste sharp subject on blurred background
        bg.paste(subject, (0, 0), subject)

        bot.edit_message_text(
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            text="📤 Uploading..."
        )

        # Save as JPEG
        output = io.BytesIO()
        bg.convert("RGB").save(output, format="JPEG", quality=95, optimize=True)
        output.seek(0)

        bot.send_photo(
            message.chat.id,
            output,
            caption="✅ iPhone Style Blur Done!\n\n🔥 Natural Portrait Effect"
        )

        bot.edit_message_text(
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            text="✅ Completed!"
        )

    except Exception as e:
        logger.error(str(e))
        try:
            bot.edit_message_text(
                chat_id=status_msg.chat.id,
                message_id=status_msg.message_id,
                text=f"❌ Error: {str(e)[:150]}"
            )
        except:
            pass

# ========================= START FLASK =========================
if __name__ == "__main__":
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
