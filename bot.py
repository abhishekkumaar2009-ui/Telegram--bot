import os
import json
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
API_NUM_INFO = "https://sra-cybertech-pvt-ltd-api-gateway.duckdns.org/Num-info?key=SRA-DAFA2D237CD6DE96&mobile="
API_TG_NUM = "https://sra-cybertech-pvt-ltd-api-gateway.duckdns.org/Tg-num?key=SRA-C28967E03172EB18&lookup="

CHANNEL_USERNAME = "@abhisxhxzoffer"
CHANNEL_LINK = "https://t.me/abhisxhxzoffer"
BOT_USERNAME = "@abhisxhxzinfo_bot"

# Yahan apni numerical Telegram User ID daalein (/myid command chala kar check kar sakte hain):
ADMIN_ID = 0  

FOOTER_TEXT = "\n━━━━━━━━━━━━━━━━━━━━\n<b>Created by - Abhishek ( @abhisxhxz )</b>"

USERS_FILE = "users.json"
http_client = httpx.AsyncClient(timeout=35.0, limits=httpx.Limits(max_keepalive_connections=20, max_connections=50))

# --- USER PERSISTENCE ---
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        try:
            with open(USERS_FILE, "w") as f:
                json.dump(list(users), f)
        except Exception as e:
            logging.error(f"Error saving user: {e}")

# --- CHANNEL SUBSCRIPTION CHECK ---
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

def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📱 Numb - Info", callback_data="mode_num_info"),
            InlineKeyboardButton("🔎 Username - Number", callback_data="mode_tg_num"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- STRICT KEY EXTRACTOR LOGIC ---
def extract_field(flat_data, exact_keys, contains_keys=None, exclude_words=None):
    if contains_keys is None:
        contains_keys = []
    if exclude_words is None:
        exclude_words = []

    # 1. Exact match priority
    for k in exact_keys:
        if k in flat_data:
            val = flat_data[k]
            if val and val.lower() not in ["none", "null", "", "false", "undefined"]:
                return val

    # 2. Contains match with negative filters
    for k, v in flat_data.items():
        if any(exc in k for exc in exclude_words):
            continue
        if any(c in k for c in contains_keys):
            if v and v.lower() not in ["none", "null", "", "false", "undefined"]:
                return v

    return None

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

    name = extract_field(
        flat_data,
        exact_keys=["name", "full_name", "fname", "customer_name", "c_name"],
        contains_keys=["name"],
        exclude_words=["father", "care_of", "co", "relative", "guardian"]
    )

    father = extract_field(
        flat_data,
        exact_keys=["father_name", "father", "fname_father", "care_of", "f_name", "guardian"],
        contains_keys=["father", "care_of", "guardian"],
        exclude_words=[]
    )

    mobile = extract_field(
        flat_data,
        exact_keys=["mobile", "phone", "number", "num", "mobile_no"],
        contains_keys=["mobile", "phone"],
        exclude_words=[]
    )

    address = extract_field(
        flat_data,
        exact_keys=["address", "addr", "permanent_address", "local_address", "location"],
        contains_keys=["address", "addr"],
        exclude_words=[]
    )

    email = extract_field(
        flat_data,
        exact_keys=["email", "mail", "email_id"],
        contains_keys=["email", "mail"],
        exclude_words=[]
    )

    sim = extract_field(
        flat_data,
        exact_keys=["operator", "carrier", "sim", "telecom", "circle"],
        contains_keys=["operator", "carrier", "circle"],
        exclude_words=[]
    )

    dob = extract_field(
        flat_data,
        exact_keys=["dob", "date_of_birth", "birth_date"],
        contains_keys=["dob", "birth"],
        exclude_words=[]
    )

    uid = extract_field(
        flat_data,
        exact_keys=["id", "uid", "aadhaar", "aadhar", "pan", "id_number", "card_no", "identity"],
        contains_keys=["aadhaar", "aadhar", "uid", "id_number", "card_no"],
        exclude_words=[]
    )

    lines = ["⚡ <b>Details Fetched by Abhishek</b>\n"]

    if name:
        lines.append(f"👤 <b>Name:</b> <code>{name}</code>")
    if father:
        lines.append(f"👨‍👦 <b>Father:</b> <code>{father}</code>")
    if mobile:
        lines.append(f"📞 <b>Mobile:</b> <code>{mobile}</code>")
    if address:
        lines.append(f"🏠 <b>Address:</b> <code>{address}</code>")
    if email:
        lines.append(f"📧 <b>Email:</b> <code>{email}</code>")
    if sim:
        lines.append(f"📡 <b>SIM/Circle:</b> <code>{sim}</code>")
    if dob:
        lines.append(f"📅 <b>DOB:</b> <code>{dob}</code>")
    if uid:
        lines.append(f"🪪 <b>ID/Aadhaar:</b> <code>{uid}</code>")

    if len(lines) == 1:
        for k, v in flat_data.items():
            if v and k not in ["status", "success", "response_code", "message"] and v.lower() not in ["none", "null", ""]:
                lines.append(f"🔹 <b>{k.title()}:</b> <code>{v}</code>")

    if len(lines) == 1:
        return None

    return "\n".join(lines)

async def fetch_api_with_retry(url, retries=2):
    for attempt in range(retries):
        try:
            response = await http_client.get(url)
            return response
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt == retries - 1:
                raise
            await asyncio.sleep(1.5)
    return None

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id)
    joined = await is_subscribed(context.bot, user.id)

    if not joined:
        text = (
            f"👋 <b>Namaste {user.first_name}!</b>\n\n"
            "⚠️ <b>Access Restricted!</b>\n"
            "Bot use karne ke liye pehle hamara channel join karein.\n\n"
            "Niche button par click karke channel join karein, fir <b>'Joined / Verify'</b> dabayein."
        )
        await update.message.reply_text(text, reply_markup=get_join_keyboard(), parse_mode="HTML")
        return

    welcome_msg = (
        f"👋 <b>Namaste {user.first_name}!</b>\n\n"
        "✅ <b>Access Verified!</b>\n\n"
        "Niche diye gaye options me se select karein ki aap kya check karna chahte hain 👇"
        f"{FOOTER_TEXT}"
    )
    await update.message.reply_text(welcome_msg, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"🆔 <b>Aapki Telegram User ID:</b> <code>{user_id}</code>", parse_mode="HTML")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if ADMIN_ID == 0 or user_id != ADMIN_ID:
        await update.message.reply_text("⛔ <b>Access Denied!</b> Sirf bot owner hi broadcast kar sakta hai.", parse_mode="HTML")
        return

    if not context.args:
        await update.message.reply_text("⚠️ <b>Format:</b> <code>/broadcast Aapka message yahan likhein</code>", parse_mode="HTML")
        return

    msg_to_send = " ".join(context.args)
    users = load_users()
    total = len(users)
    success = 0
    failed = 0

    status_msg = await update.message.reply_text(f"⏳ Broadcasting to {total} users...")

    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg_to_send, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"📢 <b>Broadcast Complete!</b>\n\n"
        f"👥 Total Users: {total}\n"
        f"✅ Sent: {success}\n"
        f"❌ Failed (Blocked): {failed}",
        parse_mode="HTML"
    )

# --- CALLBACK HANDLERS ---

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "check_join":
        joined = await is_subscribed(context.bot, user_id)
        if joined:
            save_user(user_id)
            await query.answer("✅ Verification Successful! Access unlock ho gaya.", show_alert=True)
            welcome_msg = (
                f"🎉 <b>Swagat hai {query.from_user.first_name}!</b>\n\n"
                "Niche diye gaye options me se chunein 👇"
                f"{FOOTER_TEXT}"
            )
            await query.edit_message_text(welcome_msg, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
        else:
            await query.answer("❌ Aapne abhi tak channel join nahi kiya! Kripya pehle join karein.", show_alert=True)

    elif data == "mode_num_info":
        context.user_data["mode"] = "num_info"
        await query.answer()
        await query.message.reply_text(
            "📱 <b>Numb - Info Selected</b>\n\n"
            "Kripya kisi bhi vyakti ka <b>10-digit mobile number</b> bhejein details pane ke liye:",
            parse_mode="HTML"
        )

    elif data == "mode_tg_num":
        context.user_data["mode"] = "tg_num"
        await query.answer()
        await query.message.reply_text(
            "🔎 <b>Username - Number Selected</b>\n\n"
            "Kripya Telegram user ka <b>@username</b> bhejein (jaise: <code>@username</code> ya <code>username</code>):",
            parse_mode="HTML"
        )

# --- MESSAGE PROCESSING HANDLER ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)

    joined = await is_subscribed(context.bot, user_id)
    if not joined:
        text = "⚠️ <b>Access Restricted!</b>\n\nBot use karne ke liye pehle hamara channel join karein."
        await update.message.reply_text(text, reply_markup=get_join_keyboard(), parse_mode="HTML")
        return

    text = update.message.text.strip()
    mode = context.user_data.get("mode")

    # 1. USERNAME TO NUMBER LOOKUP
    if mode == "tg_num" or text.startswith("@") or (not text.isdigit() and len(text) > 3):
        clean_user = text.lstrip("@").strip()
        
        status_msg = await update.message.reply_text(
            "⏳ <i>Fetching number from Telegram Database... Thoda samay lag sakta hai...</i>",
            parse_mode="HTML"
        )
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        try:
            url = f"{API_TG_NUM}{clean_user}"
            response = await fetch_api_with_retry(url, retries=2)
            
            raw_data = None
            try:
                raw_data = response.json()
            except Exception:
                raw_data = response.text

            found_number = None
            if isinstance(raw_data, dict):
                found_number = extract_field(
                    raw_data,
                    exact_keys=["phone", "mobile", "number", "num", "phone_number"],
                    contains_keys=["phone", "mobile", "num"]
                )
            elif isinstance(raw_data, str) and any(c.isdigit() for c in raw_data):
                found_number = "".join(filter(str.isdigit, raw_data))

            if found_number:
                reply = (
                    "🎯 <b>TELEGRAM NUMBER FOUND:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🏷 <b>Username:</b> <code>@{clean_user}</code>\n"
                    f"📞 <b>Mobile Number:</b> <code>{found_number}</code>\n\n"
                    "<i>Tip: Aap is number ko 'Numb - Info' me check karke poori details nikaal sakte hain.</i>\n"
                    f"{FOOTER_TEXT}"
                )
            else:
                reply = (
                    f"❌ <b>Username <code>@{clean_user}</code> ka number nahi mila.</b>\n\n"
                    "Ho sakta hai account private ho ya database me updated na ho."
                    f"{FOOTER_TEXT}"
                )

        except (httpx.TimeoutException, httpx.NetworkError):
            reply = (
                "⏱️ <b>Server Response Timeout!</b>\n"
                "API server response dene me zyada samay le raha hai. Kripya 1 minute baad dobara try karein."
                f"{FOOTER_TEXT}"
            )
        except Exception as e:
            reply = f"❌ Error: <code>{str(e)}</code>{FOOTER_TEXT}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Main Menu", callback_data="check_join")]
        ])
        try:
            await status_msg.edit_text(reply, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(reply, reply_markup=keyboard, parse_mode="HTML")
        return

    # 2. NUMBER TO INFO LOOKUP
    digits_only = "".join(filter(str.isdigit, text))
    if len(digits_only) < 10:
        await update.message.reply_text(
            "⚠️ Kripya sahi 10-digit mobile number bhejien ya menu se option select karein.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    target_number = digits_only[-10:]
    status_msg = await update.message.reply_text("🔍 <i>Searching in Database... Please wait...</i>", parse_mode="HTML")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        url = f"{API_NUM_INFO}{target_number}"
        response = await fetch_api_with_retry(url, retries=2)
        formatted_info = None

        try:
            raw_data = response.json()
            formatted_info = format_clean_details(raw_data)
        except Exception:
            raw_text = response.text.strip()
            if raw_text and "not found" not in raw_text.lower():
                formatted_info = raw_text

        if not formatted_info:
            reply = (
                f"❌ <b>Is number (<code>{target_number}</code>) ki koi jankari nahi mili.</b>\n"
                "Kripya number check karein ya doosra number try karein."
                f"{FOOTER_TEXT}"
            )
        else:
            reply = f"{formatted_info}\n{FOOTER_TEXT}"

    except (httpx.TimeoutException, httpx.NetworkError):
        reply = f"⏱️ Request timeout. Thodi der baad dobara koshish karein.{FOOTER_TEXT}"
    except Exception as e:
        reply = f"❌ Error: <code>{str(e)}</code>{FOOTER_TEXT}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Main Menu", callback_data="check_join")]
    ])
    try:
        await status_msg.edit_text(reply, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(reply, reply_markup=keyboard, parse_mode="HTML")

# --- RENDER WEB SERVER ---
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

# --- KEEP-ALIVE SELF PINGER ---
async def keep_alive_ping():
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not render_url:
        return
    while True:
        await asyncio.sleep(600)
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
        .connect_timeout(35.0)
        .read_timeout(35.0)
        .write_timeout(35.0)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
