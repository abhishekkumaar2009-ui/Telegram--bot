import logging
import httpx
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "8929514969:AAFTY3B5dughEyhsYzxPbSPaYnIT2HdzAsc"
API_BASE_URL = "https://sra-cybertech-pvt-ltd-api-gateway.duckdns.org/Num-info?key=SRA-DAFA2D237CD6DE96&mobile="

FOOTER_TEXT = "\n━━━━━━━━━━━━━━━━━━━━\n<b>Created by - Abhishek ( @abhisxhxz)</b>"

http_client = httpx.AsyncClient(timeout=15.0)

def get_emoji(key):
    k = key.lower()
    if any(x in k for x in ["name", "fname", "full_name"]) and "father" not in k:
        return "👤"
    if "father" in k:
        return "👨‍👦"
    if any(x in k for x in ["mobile", "phone", "number", "num"]):
        return "📞"
    if any(x in k for x in ["address", "addr", "location", "city", "state", "pincode"]):
        return "🏠"
    if any(x in k for x in ["mail", "email"]):
        return "📧"
    if any(x in k for x in ["dob", "date", "birth"]):
        return "📅"
    if any(x in k for x in ["gender", "sex"]):
        return "⚧"
    if any(x in k for x in ["operator", "carrier", "sim"]):
        return "📡"
    if any(x in k for x in ["circle", "region"]):
        return "📍"
    if any(x in k for x in ["id", "uid", "aadhaar", "pan"]):
        return "🪪"
    return "🔹"

def format_data(data):
    lines = []
    if isinstance(data, dict):
        for k, v in data.items():
            if str(k).lower() in ["status", "success", "response_code", "message"]:
                continue
            
            clean_key = str(k).replace("_", " ").title()
            emoji = get_emoji(str(k))
            
            if isinstance(v, (dict, list)):
                nested_info = format_data(v)
                if nested_info.strip():
                    lines.append(f"{emoji} <b>{clean_key}:</b>\n{nested_info}")
            else:
                if v is not None and str(v).strip() != "":
                    lines.append(f"{emoji} <b>{clean_key}:</b> {v}")
                    
        return "\n\n".join(lines)
        
    elif isinstance(data, list):
        items = [format_data(item) for item in data if item]
        return "\n\n".join(items)
        
    else:
        return str(data)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    welcome_msg = (
        f"👋 <b>Namaste {user}!</b>\n\n"
        "🔎 Mujhe koi bhi 10-digit mobile number bhejein, main uski details nikaal kar dunga."
        f"{FOOTER_TEXT}"
    )
    await update.message.reply_text(welcome_msg, parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    digits_only = "".join(filter(str.isdigit, text))

    if len(digits_only) < 10:
        await update.message.reply_text("❌ Kripya sahi 10-digit number enter karein.")
        return

    target_number = digits_only[-10:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        url = f"{API_BASE_URL}{target_number}"
        response = await http_client.get(url)
        
        try:
            data = response.json()
            formatted_info = format_data(data)
        except Exception:
            formatted_info = response.text

        if not formatted_info.strip():
            formatted_info = "❌ Is number ki koi jankari nahi mili."

        reply = (
            "📋 <b>DETAILS FOUND:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{formatted_info}\n"
            f"{FOOTER_TEXT}"
        )

    except httpx.TimeoutException:
        reply = f"⏱️ Request timeout ho gaya. Kripya thodi der baad dobara koshish karein.{FOOTER_TEXT}"
    except Exception as e:
        reply = f"❌ Error: <code>{str(e)}</code>{FOOTER_TEXT}"

    try:
        await update.message.reply_text(reply, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(reply)

if __name__ == '__main__':
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot start ho gaya hai...")
    app.run_polling(drop_pending_updates=True)
