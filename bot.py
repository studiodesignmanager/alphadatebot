import logging
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# Загрузка переменных окружения
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

if not BOT_TOKEN:
    raise RuntimeError("Error: BOT_TOKEN environment variable is not set!")

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
LANGUAGE, QUESTION1, QUESTION2 = range(3)

# Загрузка текстов из файла
TEXTS_FILE = "texts.json"
if not os.path.exists(TEXTS_FILE):
    raise FileNotFoundError("Файл texts.json не найден!")

with open(TEXTS_FILE, "r", encoding="utf-8") as f:
    texts = json.load(f)

user_data_store = {}

def save_texts():
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(texts, f, indent=2, ensure_ascii=False)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["РУССКИЙ", "ENGLISH"]]
    await update.message.reply_text(
        "Выберите язык / Choose your language:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    )
    return LANGUAGE


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text
    if lang not in ["РУССКИЙ", "ENGLISH"]:
        await update.message.reply_text("Пожалуйста, выберите язык с помощью кнопок.")
        return LANGUAGE

    context.user_data["lang"] = "ru" if lang == "РУССКИЙ" else "en"
    q1 = texts[context.user_data["lang"]]["question_1"]
    await update.message.reply_text(q1, reply_markup=ReplyKeyboardRemove())
    return QUESTION1


async def question1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer_1"] = update.message.text
    q2 = texts[context.user_data["lang"]]["question_2"]
    await update.message.reply_text(q2)
    return QUESTION2


async def question2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer_2"] = update.message.text
    lang = context.user_data["lang"]
    final = texts[lang]["final"]
    await update.message.reply_text(final)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# === Админка ===

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Доступ запрещен.")
        return

    message = "Текущие тексты:\n"
    for lang, parts in texts.items():
        message += f"\n[{lang.upper()}]\n"
        for key, val in parts.items():
            message += f"{key}: {val}\n"
    message += "\nЧтобы изменить текст, отправьте в формате:\nLANG|KEY|NEW_TEXT\nПример: ru|question_1|Новый текст"
    await update.message.reply_text(message)


async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return

    try:
        lang, key, new_text = update.message.text.split("|", 2)
        if lang in texts and key in texts[lang]:
            texts[lang][key] = new_text
            save_texts()
            await update.message.reply_text("Текст обновлен.")
        else:
            await update.message.reply_text("Неверный ключ или язык.")
    except Exception:
        await update.message.reply_text("Ошибка формата. Используйте: lang|key|new_text")


# === Запуск ===

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            QUESTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question1)],
            QUESTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question2)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("edit", edit))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit))

    logger.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()




