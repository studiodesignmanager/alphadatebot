import json
import os
from dotenv import load_dotenv
import logging

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка токена и ID из .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN or not ADMIN_ID:
    raise ValueError("⛔ TELEGRAM_TOKEN и ADMIN_ID должны быть заданы в .env")

# Функция для загрузки текстов из settings.json
def load_texts():
    with open("settings.json", "r", encoding="utf-8") as f:
        return json.load(f)

texts = load_texts()

application = ApplicationBuilder().token(TOKEN).build()
user_data = {}

# Обработчик команды /start — показывает выбор языка
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_data[chat_id] = None
    keyboard = [["🇷🇺  Русский", "🇬🇧  English"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите язык / Choose language"
    )
    await update.message.reply_text("🌍 Выберите язык / Choose your language:", reply_markup=reply_markup)

# Обработка выбора языка и показ приветствия + описание
async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    lang = "ru" if "Русский" in update.message.text else "en"
    user_data[chat_id] = lang

    welcome_key = f"welcome_{lang}"
    features_key = f"features_{lang}"

    await update.message.reply_text(
        texts.get(welcome_key, "Добро пожаловать!"),
        reply_markup=ReplyKeyboardRemove()
    )
    await update.message.reply_text(texts.get(features_key, "Что умеет этот бот?"))

# Команда /settext для админа — изменение текста в settings.json
async def set_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 У вас нет доступа.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Использование: /settext ключ текст\nПример: /settext welcome_ru Привет!")
        return

    key = args[0]
    new_text = " ".join(args[1:])
    texts[key] = new_text

    with open("settings.json", "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(f"✅ Текст '{key}' обновлён.")

# Регистрация обработчиков
application.add_handler(CommandHandler("start", start_handler))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(🇷🇺  Русский|🇬🇧  English)$"), choose_language))
application.add_handler(CommandHandler("settext", set_text))

logger.info("🚀 Bot is starting...")
application.run_polling()


