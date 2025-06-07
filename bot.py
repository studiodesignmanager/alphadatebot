from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
    chat_id = update.message.chat_id
    user_data[chat_id] = None  # сброс предыдущего языка
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
    await update.message.reply_text(
        LANGUAGE_TEXTS[lang]['welcome'],
        reply_markup=ReplyKeyboardRemove()
    )
    await update.message.reply_text(LANGUAGE_TEXTS[lang]['features'])

# Команда /settings — меню настроек для админа
async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к настройкам.")
        return

    keyboard = [
        ["Редактировать приветствие", "Редактировать текст возможностей"],
        ["Закрыть"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("⚙️ Настройки бота. Выберите, что хотите изменить:", reply_markup=reply_markup)

# Обработка выбора в меню настроек
async def settings_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    text = update.message.text
    chat_id = update.message.chat_id

    if text == "Редактировать приветствие":
        lang = user_data.get(chat_id, "ru")  # язык пользователя или по умолчанию
        await update.message.reply_text(f"Введите новый текст приветствия на {lang.upper()}:", reply_markup=ReplyKeyboardRemove())
        context.user_data["editing"] = "welcome"
    elif text == "Редактировать текст возможностей":
        lang = user_data.get(chat_id, "ru")
        await update.message.reply_text(f"Введите новый текст возможностей на {lang.upper()}:", reply_markup=ReplyKeyboardRemove())
        context.user_data["editing"] = "features"
    elif text == "Закрыть":
        await update.message.reply_text("Настройки закрыты.", reply_markup=ReplyKeyboardRemove())
        context.user_data.pop("editing", None)

# Обработка введенного текста для обновления LANGUAGE_TEXTS
async def text_edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    chat_id = update.message.chat_id
    editing_key = context.user_data.get("editing")
    if not editing_key:
        return

    lang = user_data.get(chat_id, "ru")  # язык
    new_text = update.message.text

    LANGUAGE_TEXTS[lang][editing_key] = new_text
    await update.message.reply_text(f"Текст '{editing_key}' на языке {lang.upper()} успешно обновлен.")
    context.user_data.pop("editing", None)

# Регистрация хендлеров
application.add_handler(CommandHandler("start", start_handler))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(🇷🇺  Русский|🇬🇧  English)$"), choose_language))

application.add_handler(CommandHandler("settings", settings_handler))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Редактировать приветствие|Редактировать текст возможностей|Закрыть)$"), settings_choice_handler))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_edit_handler))

logger.info("🚀 Bot is starting...")
application.run_polling()

