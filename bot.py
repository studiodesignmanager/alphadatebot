
import logging
import json
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)

LANGUAGE, QUESTION1, QUESTION2 = range(3)

# Загрузка текстов
def load_texts():
    with open("texts.json", "r", encoding="utf-8") as f:
        return json.load(f)

# Сохранение текстов
def save_texts(data):
    with open("texts.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

texts_data = load_texts()

user_language = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton(texts_data["LANGUAGE_CHOICES"]["ru"]),
          KeyboardButton(texts_data["LANGUAGE_CHOICES"]["en"])]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(texts_data["texts"]["en"]["welcome"], reply_markup=reply_markup)
    return LANGUAGE

# Обработка выбора языка
async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lang_code = "ru" if text == texts_data["LANGUAGE_CHOICES"]["ru"] else "en"
    user_language[update.effective_user.id] = lang_code

    await update.message.reply_text(texts_data["texts"][lang_code]["question1"])
    return QUESTION1

# Ответ на 1-й вопрос
async def handle_question1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_language.get(update.effective_user.id, "en")
    await update.message.reply_text(texts_data["texts"][lang]["question2"])
    return QUESTION2

# Ответ на 2-й вопрос
async def handle_question2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_language.get(update.effective_user.id, "en")
    await update.message.reply_text(texts_data["texts"][lang]["thanks"])
    return ConversationHandler.END

# Команда /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return

    message = "⚙️ Admin Panel\n\n"

    for lang_code in ["ru", "en"]:
        message += f"\nLanguage: {lang_code.upper()}\n"
        for key in texts_data["texts"][lang_code]:
            message += f"{key}: {texts_data['texts'][lang_code][key]}\n"

    message += "\nSend a message in this format to update:\n<lang> <key> = <new_text>\nExample:\nru question1 = Новый текст"
    await update.message.reply_text(message)

# Обработка изменения текстов
async def handle_admin_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        text = update.message.text
        parts = text.split("=", 1)
        if len(parts) != 2:
            await update.message.reply_text("❌ Wrong format. Use: ru question1 = Новый текст")
            return
        left, new_text = parts
        lang, key = left.strip().split()
        new_text = new_text.strip()

        texts_data["texts"][lang][key] = new_text
        save_texts(texts_data)
        await update.message.reply_text("✅ Text updated successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            QUESTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question1)],
            QUESTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question2)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_update))

    print("✅ Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()



