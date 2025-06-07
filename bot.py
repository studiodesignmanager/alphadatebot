from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import os
from dotenv import load_dotenv
import logging

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN or not ADMIN_ID:
    raise ValueError("⛔ Убедитесь, что в .env заданы TELEGRAM_TOKEN и ADMIN_ID")

application = ApplicationBuilder().token(TOKEN).build()
user_data = {}

LANGUAGE_TEXTS = {
    'ru': {
        'welcome': "👋 Добро пожаловать!\n\nЭтот бот поможет вам сделать первый шаг к новым отношениям.\nОн задаст несколько простых вопросов, чтобы лучше понять ваши цели и ожидания в поиске партнёра.\nОтвечайте искренне — это важный шаг навстречу новому знакомству 💖",
        'features': "💡 Что умеет этот бот?\n\n— Поможет вам сделать первый шаг к знакомству\n— Задаст простые вопросы\n— Построит базу для поиска подходящих партнёров"
    },
    'en': {
        'welcome': "👋 Welcome!\n\nThis bot will help you take the first step toward a new relationship.\nIt will ask a few simple questions to better understand your goals and expectations when looking for a partner.\nBe honest — it's an important step toward meaningful connection 💖",
        'features': "💡 What can this bot do?\n\n— Help you take the first step toward meeting someone\n— Ask you simple personal questions\n— Lay the foundation for future matching"
    }
}

# Обработчик /start — только выбор языка
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🇷🇺  Русский", "🇬🇧  English"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите язык / Choose language"
    )
    await update.message.reply_text("🌍 Выберите язык / Choose your language:", reply_markup=reply_markup)

# После выбора языка — приветствие на нужном языке
async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    lang = "ru" if "Русский" in update.message.text else "en"
    user_data[chat_id] = lang
    await update.message.reply_text(LANGUAGE_TEXTS[lang]['welcome'])
    await update.message.reply_text(LANGUAGE_TEXTS[lang]['features'])

# Регистрация хендлеров
application.add_handler(CommandHandler("start", start_handler))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(🇷🇺  Русский|🇬🇧  English)$"), choose_language))

logger.info("🚀 Bot is starting...")
application.run_polling()
