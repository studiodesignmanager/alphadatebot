

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

# --- Загрузка .env ---
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)

if not BOT_TOKEN:
    raise RuntimeError("Error: BOT_TOKEN environment variable is not set!")

# --- Логирование ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Состояния ---
LANGUAGE, QUESTION1, QUESTION2 = range(3)

# --- Файл с текстами ---
TEXTS_FILE = Path(__file__).parent / "texts.json"
if not TEXTS_FILE.exists():
    raise FileNotFoundError("Файл texts.json не найден!")

with open(TEXTS_FILE, "r", encoding="utf-8") as f:
    texts = json.load(f)

def save_texts():
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

# --- Хендлеры ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["РУССКИЙ", "ENGLISH"]]
    await update.message.reply_text(
        "Выберите язык / Choose your language:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return LANGUAGE

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text
    if lang not in ["РУССКИЙ", "ENGLISH"]:
        await update.message.reply_text("Пожалуйста, выберите язык кнопками.")
        return LANGUAGE
    context.user_data["lang"] = "ru" if lang == "РУССКИЙ" else "en"
    await update.message.reply_text(texts[context.user_data["lang"]]["question_1"], reply_markup=ReplyKeyboardRemove())
    return QUESTION1

async def question1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer_1"] = update.message.text
    await update.message.reply_text(texts[context.user_data["lang"]]["question_2"])
    return QUESTION2

async def question2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer_2"] = update.message.text
    await update.message.reply_text(texts[context.user_data["lang"]]["final"])
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- Админка ---

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Доступ запрещен.")
        return
    msg = "Текущие тексты:\n\n"
    for lang_code, vals in texts.items():
        msg += f"[{lang_code}]\n"
        for key, val in vals.items():
            msg += f"{key}: {val}\n"
        msg += "\n"
    msg += (
        "Чтобы изменить текст, отправьте сообщение в формате:\n"
        "lang|key|новый текст\n"
        "Например:\nru|question_1|Новый текст вопроса"
    )
    await update.message.reply_text(msg)

async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return
    text = update.message.text
    try:
        lang, key, new_text = text.split("|", 2)
        lang = lang.strip().lower()
        key = key.strip()
        new_text = new_text.strip()
        if lang in texts and key in texts[lang]:
            texts[lang][key] = new_text
            save_texts()
            await update.message.reply_text("Текст успешно обновлен.")
        else:
            await update.message.reply_text("Ошибка: неверный язык или ключ.")
    except Exception:
        await update.message.reply_text("Ошибка формата. Используйте: lang|key|новый текст")

# --- Основная функция запуска ---

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

    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()




