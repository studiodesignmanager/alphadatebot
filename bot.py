import logging
import json
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.ext import CallbackContext

# Укажи здесь свой токен
BOT_TOKEN = "7110528714:AAG0mSUIkaEsbsJBL4FeCIq461HI2-xqx0g"
ADMIN_ID = 486225736

with open("texts.json", "r", encoding="utf-8") as f:
    texts = json.load(f)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANGUAGE, QUESTION_1, QUESTION_2 = range(3)

user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_keyboard = [[KeyboardButton("РУССКИЙ")], [KeyboardButton("ENGLISH")]]
    await update.message.reply_text("Выберите язык / Choose your language:", reply_markup=ReplyKeyboardMarkup(lang_keyboard, resize_keyboard=True))
    return LANGUAGE

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_lang = update.message.text
    lang_key = "ru" if selected_lang == "РУССКИЙ" else "en"
    context.user_data["lang"] = lang_key

    await update.message.reply_text(texts[lang_key]["question_1"], reply_markup=ReplyKeyboardRemove())
    return QUESTION_1

async def question_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer1"] = update.message.text
    await send_to_admin(update, context, question="1")

    lang_key = context.user_data["lang"]
    await update.message.reply_text(texts[lang_key]["question_2"])
    return QUESTION_2

async def question_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer2"] = update.message.text
    await send_to_admin(update, context, question="2")

    lang_key = context.user_data["lang"]
    await update.message.reply_text(texts[lang_key]["final"])
    return ConversationHandler.END

async def send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, question):
    user = update.message.from_user
    username = f"@{user.username}" if user.username else f"https://t.me/user?id={user.id}"
    answer = update.message.text
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Ответ пользователя {username} на вопрос {question}: {answer}")

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Настройки:\n(реализация редактирования позже)")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            QUESTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_1)],
            QUESTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_2)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("settings", settings))

    app.run_polling()

if __name__ == "__main__":
    main()










