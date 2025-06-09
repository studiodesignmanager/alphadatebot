import json
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 486225736

# Состояния для ConversationHandler
LANGUAGE, QUESTION_1, QUESTION_2, SETTINGS = range(4)

with open("texts.json", "r", encoding="utf-8") as f:
    texts = json.load(f)

user_lang = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["РУССКИЙ", "ENGLISH"]]
    await update.message.reply_text(
        "Выберите язык / Choose language",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return LANGUAGE

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text.lower()
    if lang.startswith("рус"):
        lang_key = "ru"
    elif lang.startswith("en"):
        lang_key = "en"
    else:
        await update.message.reply_text("Пожалуйста, выберите язык из кнопок.")
        return LANGUAGE

    user_lang[update.effective_user.id] = lang_key
    await update.message.reply_text(texts[lang_key]["question_1"], reply_markup=ReplyKeyboardRemove())
    return QUESTION_1

async def handle_q1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q1"] = update.message.text
    lang_key = user_lang.get(update.effective_user.id, "en")

    user = update.effective_user
    username_or_link = f"@{user.username}" if user.username else f"https://t.me/user?id={user.id}"

    # Отправляем админу сразу ответ №1
    msg1 = f"Ответ №1 от {username_or_link}:\n{update.message.text}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg1)

    await update.message.reply_text(texts[lang_key]["question_2"])
    return QUESTION_2

async def handle_q2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q2"] = update.message.text
    lang_key = user_lang.get(update.effective_user.id, "en")

    user = update.effective_user
    username_or_link = f"@{user.username}" if user.username else f"https://t.me/user?id={user.id}"

    # Отправляем админу сразу ответ №2
    msg2 = f"Ответ №2 от {username_or_link}:\n{update.message.text}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg2)

    await update.message.reply_text(texts[lang_key]["final"])
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Команда /settings для админа
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Недоступно")
        return ConversationHandler.END

    keyboard = [[f"{lang.upper()} - {key}"] for lang in texts for key in texts[lang]]
    await update.message.reply_text("Выберите текст для редактирования:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SETTINGS

def main():
    import os

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("Please set BOT_TOKEN environment variable")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            QUESTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_q1)],
            QUESTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_q2)],
            SETTINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel)],  # Заглушка
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("settings", settings))

    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()









