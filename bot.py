import json
import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

LANGUAGE, QUESTION_1, QUESTION_2 = range(3)

with open("texts.json", "r", encoding="utf-8") as f:
    texts = json.load(f)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 486225736

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("РУССКИЙ")], [KeyboardButton("ENGLISH")]]
    await update.message.reply_text("Choose language / Выберите язык:",
                                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return LANGUAGE

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text
    lang_key = "ru" if "РУССКИЙ" in lang else "en"
    context.user_data['lang'] = lang_key

    await update.message.reply_text(texts[lang_key]["question_1"], reply_markup=ReplyKeyboardRemove())
    return QUESTION_1

async def question_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['answer1'] = update.message.text
    await notify_admin(update, context, "question_1", update.message.text)

    lang_key = context.user_data['lang']
    await update.message.reply_text(texts[lang_key]["question_2"])
    return QUESTION_2

async def question_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['answer2'] = update.message.text
    await notify_admin(update, context, "question_2", update.message.text)

    lang_key = context.user_data['lang']
    await update.message.reply_text(texts[lang_key]["final"])
    return ConversationHandler.END

async def notify_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str, answer: str):
    user = update.effective_user
    lang_key = context.user_data['lang']
    question_text = texts[lang_key][question]

    sender = f"@{user.username}" if user.username else f"[User without username](tg://user?id={user.id})"
    message = f"{sender} answered:\n\n*{question_text}*\n{answer}"

    await context.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode="Markdown")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = [[KeyboardButton("Настройки")]]
    await update.message.reply_text("Админ-панель:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = "Тексты:\n"
    for lang in texts:
        text += f"\n[{lang.upper()}]\n"
        for key, val in texts[lang].items():
            text += f"{key}: {val}\n"
    await update.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог отменён.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    if not BOT_TOKEN:
        raise ValueError("Please set BOT_TOKEN environment variable")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            QUESTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_1)],
            QUESTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_2)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.Regex("^(Настройки)$"), handle_settings))

    app.run_polling()

if __name__ == '__main__':
    main()










