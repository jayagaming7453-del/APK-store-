import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ── CONFIG ── Apna token aur chat ID yahan daalo ──
BOT_TOKEN = "8757579531:AAF41niEfnprPh-4tGBiGOwqnWy4seTiCjU"   # BotFather se mila token
ADMIN_CHAT_ID = 8331635823        # Apna Chat ID (number)

# APK data file
DATA_FILE = "apks.json"

# ── HELPERS ──────────────────────────────────────────────
def load_apks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_apks(apks):
    with open(DATA_FILE, "w") as f:
        json.dump(apks, f, indent=2)

def is_admin(update: Update) -> bool:
    return update.effective_chat.id == ADMIN_CHAT_ID

# ── STATES (per user) ────────────────────────────────────
user_state = {}   # { chat_id: { step, data } }

# ── /start ───────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ Aap admin nahi hain.")
        return
    await update.message.reply_text(
        "👋 *APK Store Bot*\n\n"
        "Commands:\n"
        "📦 /upload — Naya APK add karo\n"
        "📋 /list — Saare APKs dekho\n"
        "🗑 /delete — APK delete karo\n"
        "🌐 /site — Website link dekho",
        parse_mode="Markdown"
    )

# ── /upload ──────────────────────────────────────────────
async def upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    user_state[update.effective_chat.id] = {"step": "waiting_name", "data": {}}
    await update.message.reply_text("✏️ *Step 1/4:* App ka naam likho\n_(e.g. MyApp v2.0)_", parse_mode="Markdown")

# ── /list ─────────────────────────────────────────────────
async def list_apks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    apks = load_apks()
    if not apks:
        await update.message.reply_text("📭 Koi APK nahi hai abhi.")
        return
    msg = "📋 *Uploaded APKs:*\n\n"
    for i, apk in enumerate(apks):
        msg += f"{i+1}. *{apk['name']}* — ID: `{apk['id']}`\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# ── /delete ───────────────────────────────────────────────
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    apks = load_apks()
    if not apks:
        await update.message.reply_text("📭 Delete karne ke liye koi APK nahi.")
        return
    buttons = []
    for apk in apks:
        buttons.append([InlineKeyboardButton(f"🗑 {apk['name']}", callback_data=f"del_{apk['id']}")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="del_cancel")])
    await update.message.reply_text("🗑 *Kaunsa APK delete karein?*", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "del_cancel":
        await query.edit_message_text("❌ Cancel kar diya.")
        return
    apk_id = int(query.data.replace("del_", ""))
    apks = load_apks()
    apks = [a for a in apks if a["id"] != apk_id]
    save_apks(apks)
    await query.edit_message_text("✅ APK delete ho gaya!")

# ── /site ─────────────────────────────────────────────────
async def site_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await update.message.reply_text(
        "🌐 *Website:*\nApni Railway URL yahan add karo.\n\n"
        "Deploy ke baad Railway dashboard se URL milega.",
        parse_mode="Markdown"
    )

# ── MESSAGE HANDLER (upload flow) ────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    chat_id = update.effective_chat.id
    state = user_state.get(chat_id)
    if not state:
        await update.message.reply_text("📌 /upload se shuru karo ya /start likhke commands dekho.")
        return

    step = state["step"]

    # Step 1: App name
    if step == "waiting_name":
        state["data"]["name"] = update.message.text.strip()
        state["step"] = "waiting_badge"
        buttons = [
            [InlineKeyboardButton("🆕 NEW", callback_data="badge_new"),
             InlineKeyboardButton("🔥 HOT", callback_data="badge_hot")],
            [InlineKeyboardButton("⭐ PRO", callback_data="badge_pro"),
             InlineKeyboardButton("👑 VIP", callback_data="badge_vip")],
            [InlineKeyboardButton("🔧 MOD", callback_data="badge_mod"),
             InlineKeyboardButton("➖ None", callback_data="badge_none")],
        ]
        await update.message.reply_text("🏷 *Step 2/4:* Badge select karo:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    # Step 3: Telegram link (optional)
    elif step == "waiting_tg":
        txt = update.message.text.strip()
        state["data"]["tg"] = "" if txt.lower() in ["skip","-","no"] else txt
        state["step"] = "waiting_support"
        await update.message.reply_text("📩 *Step 3b:* Support link daalo _(ya 'skip' likho)_", parse_mode="Markdown")

    elif step == "waiting_support":
        txt = update.message.text.strip()
        state["data"]["support"] = "" if txt.lower() in ["skip","-","no"] else txt
        state["step"] = "waiting_video"
        await update.message.reply_text("▶️ *Step 3c:* Video link daalo _(ya 'skip' likho)_", parse_mode="Markdown")

    elif step == "waiting_video":
        txt = update.message.text.strip()
        state["data"]["video"] = "" if txt.lower() in ["skip","-","no"] else txt
        state["step"] = "waiting_photo"
        await update.message.reply_text("🖼 *Step 3/4:* App ka photo/icon bhejo", parse_mode="Markdown")

    # Step 5: APK file
    elif step == "waiting_apk":
        if update.message.document:
            doc = update.message.document
            if doc.file_name and doc.file_name.endswith(".apk"):
                await update.message.reply_text("⏳ APK download ho raha hai...")
                file = await doc.get_file()
                os.makedirs("static/apks", exist_ok=True)
                apk_path = f"static/apks/{doc.file_name}"
                await file.download_to_drive(apk_path)
                state["data"]["apk_path"] = apk_path
                state["data"]["file_name"] = doc.file_name
                # Save to JSON
                import time
                from datetime import datetime
                apks = load_apks()
                new_apk = {
                    "id": int(time.time() * 1000),
                    "name": state["data"]["name"],
                    "badge": state["data"].get("badge", ""),
                    "tg": state["data"].get("tg", ""),
                    "support": state["data"].get("support", ""),
                    "video": state["data"].get("video", ""),
                    "img_path": state["data"].get("img_path", ""),
                    "apk_path": apk_path,
                    "file_name": doc.file_name,
                    "date": datetime.now().strftime("%d/%m/%Y")
                }
                apks.insert(0, new_apk)
                save_apks(apks)
                user_state.pop(chat_id, None)
                await update.message.reply_text(
                    f"✅ *APK upload ho gaya!*\n\n"
                    f"📦 *{new_apk['name']}*\n"
                    f"📁 File: `{doc.file_name}`\n"
                    f"🌐 Ab website pe dikh raha hai!",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Sirf .apk file bhejo!")
        else:
            await update.message.reply_text("❌ Document file bhejo (.apk)")

# ── PHOTO HANDLER ─────────────────────────────────────────
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    chat_id = update.effective_chat.id
    state = user_state.get(chat_id)
    if not state or state["step"] != "waiting_photo":
        return
    photo = update.message.photo[-1]
    file = await photo.get_file()
    os.makedirs("static/imgs", exist_ok=True)
    img_path = f"static/imgs/{photo.file_id}.jpg"
    await file.download_to_drive(img_path)
    state["data"]["img_path"] = img_path
    state["step"] = "waiting_apk"
    await update.message.reply_text("📦 *Step 4/4:* Ab APK file bhejo (.apk)", parse_mode="Markdown")

# ── BADGE CALLBACK ────────────────────────────────────────
async def badge_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    state = user_state.get(chat_id)
    if not state:
        return
    badge = query.data.replace("badge_", "")
    state["data"]["badge"] = "" if badge == "none" else badge
    state["step"] = "waiting_tg"
    await query.edit_message_text(
        f"✅ Badge: *{badge.upper()}*\n\n💬 *Step 3/4:* Telegram channel link daalo _(ya 'skip' likho)_",
        parse_mode="Markdown"
    )

# ── MAIN ─────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload_start))
    app.add_handler(CommandHandler("list", list_apks))
    app.add_handler(CommandHandler("delete", delete_start))
    app.add_handler(CommandHandler("site", site_link))
    app.add_handler(CallbackQueryHandler(delete_callback, pattern="^del_"))
    app.add_handler(CallbackQueryHandler(badge_callback, pattern="^badge_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.TEXT, handle_message))
    print("🤖 Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
