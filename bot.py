import os
import asyncio
import logging
import httpx
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction, ChatMemberStatus
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# --- CONFIGURATION ---
BOT_TOKEN = "8929514969:AAFTY3B5dughEyhsYzxPbSPaYnIT2HdzAsc"
API_BASE_URL = "https://sra-cybertech-pvt-ltd-api-gateway.duckdns.org/Num-info?key=SRA-DAFA2D237CD6DE96&mobile="

CHANNEL_USERNAME = "@abhisxhxzoffer"
CHANNEL_LINK = "https://t.me/abhisxhxzoffer"
BOT_USERNAME = "@abhisxhxzinfo_bot"

FOOTER_TEXT = "\n━━━━━━━━━━━━━━━━━━━━\n<b>Created by - Abhishek ( @abhisxhxz )</b>"

http_client = httpx.AsyncClient(timeout=15.0)

# Check user membership
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ]
    except Exception as e:
        logging.warning(f"Subscription check error: {e}")
        return False

def get_join_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Joined / Verify", callback_data="check_join")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Short & Clean Data Formatter
def format_clean_details(data):
    if isinstance(data, list):
        if len(data) == 0:
            return None
        data = data[0]

    if not isinstance(data, dict):
        text_data = str(data).strip()
        if not text_data or "not found" in text_data.lower() or "no data" in text_data.lower():
            return None
        return text_data

    flat_data = {}
    def flatten(d):
        for k, v in d.items():
            if isinstance(v, dict):
                flatten(v)
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                flatten(v[0])
            else:
                flat_data[str(k).lower().strip()] = str(v).strip() if v is not None else ""
    flatten(data)

    def find_val(keywords):
        for k, v in flat_data.items():
            if any(kw == k or kw in k for kw in keywords):
                if v and v.lower() not in ["none", "null", "", "false", "undefined"]:
                    return v
        return None

    name = find_val(["full_name", "fname", "name", "customer_name"])
    father = find_val(["father_name", "father", "fname_father", "care_of"])
    mobile = find_val(["mobile", "phone", "number", "num"])
    address = find_val(["address", "addr", "permanent_address", "city", "location"])
    email = find_val(["email", "mail"])
    sim = find_val(["operator", "carrier", "sim", "telecom", "circle"])
    dob = find_val(["dob", "date_of_birth", "birth"])
    uid = find_val(["aadhaar", "uid", "pan", "id"])

    lines = ["⚡ <b>Details Fetched by Abhishek</b>\n"]

    if name:
        lines.append(f"👤 <b>Name:</b> {name}")
    if father:
        lines.append(f"👨‍👦 <b>Father:</b> {father}")
    if mobile:
        lines.append(f"📞 <b>Mobile:</b> {mobile}")
    if address:
        lines.append(f"🏠 <b>Address:</b> {address}")
    if email:
        lines.append(f"📧 <b>Email:</b> {email}")
    if sim:
        lines.append(f"📡 <b>SIM/Circle:</b> {sim}")
    if dob:
        lines.append(f"📅 <b>DOB:</b> {dob}")
    if uid:
        lines.append(f"🪪 <b>ID:</b> {uid}")

    # Agar koi main field nahi mili toh baaki keys check karo
    if len(lines) == 1:
        for k, v in flat_data.items():
            if v and k not in ["status", "success", "response_code", "message"] and v.lower() not in ["none", "null", ""]:
                lines.append(f"🔹 <b>{k.title()}:</b> {v}")

    # Agar abhi bhi koi valid data nahi mila
    if len(lines) == 1:
        return None

    return "\n".join(lines)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    joined = await is_subscribed(context.bot, user.id)

    if not joined:
        text = (
            f"👋 <b>Namaste {user.first_name}!</b>\n\n"
            "⚠️ <b>Access Restricted!</b>\n"
            "Bot use karne ke liye pehle hamara channel join karna hoga.\n\n"
            "Niche button par click karke channel join karein, fir <b>'Joined / Verify'</b> dabayein."
        )
        await update.message.reply_text(text, reply_markup=get_join_keyboard(), parse_mode="HTML")
        return

    welcome_msg = (
        f"👋 <b>Namaste {user.first_name}!</b>\n\n"
        "✅ <b>Access Verified!</b>\n"
        "🔎 Mujhe koi bhi 10-digit mobile number bhejein details pane ke liye."
        f"{FOOTER_TEXT}"
    )
    await update.message.reply_text(welcome_msg, parse_mode="HTML")

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    joined = await is_subscribed(context.bot, user_id)

    if joined:
        await query.answer("✅ Verification Successful! Access unlock ho gaya.", show_alert=True)
        welcome_msg = (
            f"🎉 <b>Swagat hai {query.from_user.first_name}!</b>\n\n"
            "🔎 Ab aap koi bhi 10-digit mobile number send kar sakte hain."
            f"{FOOTER_TEXT}"
        )
        await query.edit_message_text(welcome_msg, parse_mode="HTML")
    else:
        await query.answer("❌ Aapne abhi tak channel join nahi kiya! Kripya pehle join karein.", show_alert=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    joined = await is_subscribed(context.bot, user_id)

    if not joined:
        text = "⚠️ <b>Access Restricted!</b>\n\nNumber search karne ke liye pehle channel join karna hoga."
        await update.message.reply_text(text, reply_markup=get_join_keyboard(), parse_mode="HTML")
        return

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
        formatted_info = None

        try:
            raw_data = response.json()
            formatted_info = format_clean_details(raw_data)
        except Exception:
            raw_text = response.text.strip()
            if raw_text and "not found" not in raw_text.lower():
                formatted_info = raw_text

        # Jab number ki koi details na mile
        if not formatted_info:
            reply = (
                f"❌ <b>Is number (<code>{target_number}</code>) ki koi jankari nahi mili.</b>\n"
                "Kripya number check karein ya doosra number try karein."
                f"{FOOTER_TEXT}"
            )
        else:
            reply = f"{formatted_info}\n{FOOTER_TEXT}"

    except httpx.TimeoutException:
        reply = f"⏱️ Request timeout. Thodi der baad dobara koshish karein.{FOOTER_TEXT}"
    except Exception as e:
        reply = f"❌ Error: <code>{str(e)}</code>{FOOTER_TEXT}"

    try:
        await update.message.reply_text(reply, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(reply)

# Render dummy web server
async def handle_health_check(request):
    return web.Response(text="Bot is running active 24/7!")

async def start_web_server():
    server = web.Application()
    server.router.add_get("/", handle_health_check)
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# Automatic keep-alive self pinger
async def keep_alive_ping():
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not render_url:
        return
    while True:
        await asyncio.sleep(600)  # Har 10 minute me ping karega
        try:
            await http_client.get(render_url)
            logging.info("Keep-alive self ping successful!")
        except Exception as e:
            logging.warning(f"Self-ping failed: {e}")

async def main():
    await start_web_server()
    asyncio.create_task(keep_alive_ping())

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
    
