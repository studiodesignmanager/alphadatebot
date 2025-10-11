import logging
import json
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# --- CONFIG ---
BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
ADMIN_ID = 486225736

# --- LOGGING ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- LOAD TEXTS ---
with open("texts.json", "r", encoding="utf-8") as f:
    texts = json.load(f)

# --- STATES ---
LANGUAGE, Q1, Q2, FINAL = range(4)

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["РУССКИЙ", "ENGLISH"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Пожалуйста, выберите язык / Please select a language:",
        reply_markup=markup
    )
    return LANGUAGE

# --- LANGUAGE SELECT ---
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text == "русский":
        context.user_data["lang"] = "ru"
    elif text == "english":
        context.user_data["lang"] = "en"
    else:
        await update.message.reply_text(
            "Пожалуйста, выберите язык, используя кнопки ниже / Please select using the buttons."
        )
        return LANGUAGE

    lang = context.user_data["lang"]
    await update.message.reply_text(
        texts[lang]["greeting"], reply_markup=ReplyKeyboardRemove()
    )
    await update.message.reply_text(texts[lang]["question1"])
    return Q1

# --- FIRST QUESTION ---
async def question1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer1"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["question2"])
    return Q2

# --- SECOND QUESTION ---
async def question2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer2"] = update.message.text
    lang = context.user_data["lang"]

    user = update.message.from_user
    username = f"@{user.username}" if user.username else "No username"

    # --- Message to admin ---
    msg = (
        f"📩 New response:\n"
        f"👤 {username}\n"
        f"🌐 Language: {lang.upper()}\n\n"
        f"1️⃣ {context.user_data['answer1']}\n"
        f"2️⃣ {context.user_data['answer2']}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    # --- Final message to user ---
    await update.message.reply_text(texts[lang]["final"], reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- CANCEL HANDLER ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён. / Conversation cancelled.")
    return ConversationHandler.END

# --- MAIN ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question1)],
            Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question2)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    logging.info("Bot started successfully.")
    app.run_polling()

if __name__ == "__main__":
    main()













