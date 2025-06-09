import logging
import json
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# 🔧 Настройки
BOT_TOKEN = "7110528714:AAG0mSUIkaEsbsJBL4FeCIq461HI2-xqx0g"
ADMIN_ID = 486225736

# Состояния диалога
LANGUAGE, QUESTION_1, QUESTION_2 = range(3)

# Загрузка текстов
TEXTS_FILE = "texts.json"
if os.path.exists(TEXTS_FILE):
    with open(TEXTS_FILE, "r", encoding="utf-8") as f:
        texts = json.load(f)
else:
    texts = {
        "ru": {
            "welcome_message": "Добро пожаловать! Выберите язык.",
            "question_1": "У вас были регистрации на международных сайтах знакомствах ранее?",
            "question_2": "С какой целью интересует регистрация?",
            "final": "Спасибо! Мы свяжемся с вами в ближайшее время"
        },
        "en": {
            "welcome_message": "Welcome! Please select your language.",
            "question_1": "Have you registered on any international dating sites before?",
            "question_2": "What is your reason for signing up?",
            "final": "Thank you! We will get in touch with you shortly."
        }
    }

# Логирование
logging.basicConfig(level=logging.INFO)

# Пользовательский язык
user_lang = {}

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([["РУССКИЙ", "ENGLISH"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите язык / Choose your language", reply_markup=reply_markup)
    return LANGUAGE

# Выбор языка
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_choice = update.message.text
    lang_key = "ru" if lang_choice == "РУССКИЙ" else "en"
    user_lang[update.effective_user.id] = lang_key
    await update.message.reply_text(texts[lang_key]["question_1"], reply_markup=ReplyKeyboardRemove())
    return QUESTION_1

# Ответ на 1 вопрос
async def handle_q1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q1"] = update.message.text
    lang_key = user_lang.get(update.effective_user.id, "en")
    await update.message.reply_text(texts[lang_key]["question_2"])
    return QUESTION_2

# Ответ на 2 вопрос
async def handle_q2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q1 = context.user_data.get("q1")
    q2 = update.message.text
    lang_key = user_lang.get(update.effective_user.id, "en")
    await update.message.reply_text(texts[lang_key]["final"])

    user = update.effective_user
    username_or_link = f"@{user.username}" if user.username else f"https://t.me/user?id={user.id}"

    msg = f"Новый ответ от {username_or_link}\n\n1. {q1}\n2. {q2}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

# Команда /settings только для админа
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Недоступно")
        return

    keyboard = [[f"{lang.upper()} - {key}"] for lang in texts for key in texts[lang]]
    await update.message.reply_text("Выберите текст для редактирования:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return 10  # Состояние настройки

# Обработка выбора текста для редактирования
async def select_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lang_key, text_key = update.message.text.lower().split(" - ")
        context.user_data["edit_lang"] = lang_key
        context.user_data["edit_key"] = text_key
        await update.message.reply_text(f"Отправьте новый текст для {lang_key.upper()} → {text_key}")
        return 11
    except:
        await update.message.reply_text("Неверный формат. Попробуйте снова.")
        return 10

# Обновление текста
async def update_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_key = context.user_data["edit_lang"]
    text_key = context.user_data["edit_key"]
    texts[lang_key][text_key] = update.message.text
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)
    await update.message.reply_text("Текст обновлён.")
    return ConversationHandler.END

# Главная функция
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            QUESTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_q1)],
            QUESTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_q2)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    settings_conv = ConversationHandler(
        entry_points=[CommandHandler("settings", settings)],
        states={
            10: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_text)],
            11: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(settings_conv)

    app.run_polling()

if __name__ == "__main__":
    main()








