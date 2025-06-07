import json
import os
from dotenv import load_dotenv
import logging

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN or not ADMIN_ID:
    raise ValueError("⛔ TELEGRAM_TOKEN и ADMIN_ID должны быть заданы в .env")

SETTINGS_FILE = "settings.json"

# Ключи состояний опроса
(
    LANG_CHOOSE,
    ASK_AGE_COUNTRY,
    ASK_REGISTRATION,
    ASK_PURPOSE,
    FINAL_MESSAGE,
    ADMIN_MENU,
    ADMIN_EDIT_TEXT,
) = range(7)

# Загружаем или создаём default texts
def load_texts():
    default_texts = {
        "welcome_ru": "Добрый день! Напишите пожалуйста свой возраст и страну проживания",
        "registration_question_ru": "У вас были регистрации на международных сайтах знакомствах ранее?",
        "purpose_question_ru": "С какой целью интересует регистрация?",
        "final_message_ru": "Спасибо! Мы свяжемся с вами в ближайшее время",

        "welcome_en": "Good day! Please write your age and country of residence",
        "registration_question_en": "Have you registered on international dating sites before?",
        "purpose_question_en": "What is the purpose of your registration?",
        "final_message_en": "Thank you! We will contact you shortly",

        "choose_language": "🌍 Выберите язык / Choose your language:",
        "settings_menu_title": "⚙️ Настройки текстов (только для админа)",
        "edit_prompt": "Введите новый текст для выбранного пункта:",
        "access_denied": "🚫 У вас нет доступа к этой команде.",
    }
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_texts, f, ensure_ascii=False, indent=2)
        return default_texts
    else:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

def save_texts(texts):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

texts = load_texts()

application = ApplicationBuilder().token(TOKEN).build()

# Для хранения данных пользователя и админского режима
user_data = {}

# Кнопки языка
language_keyboard = ReplyKeyboardMarkup(
    [["🇷🇺  Русский", "🇬🇧  English"]],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выберите язык / Choose language",
)

# Кнопки меню редактирования для админа
admin_menu_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("Изменить приветствие (RU)", callback_data="edit_welcome_ru"),
     InlineKeyboardButton("Edit greeting (EN)", callback_data="edit_welcome_en")],
    [InlineKeyboardButton("Изменить вопрос о регистрации (RU)", callback_data="edit_registration_question_ru"),
     InlineKeyboardButton("Edit registration question (EN)", callback_data="edit_registration_question_en")],
    [InlineKeyboardButton("Изменить цель регистрации (RU)", callback_data="edit_purpose_question_ru"),
     InlineKeyboardButton("Edit purpose question (EN)", callback_data="edit_purpose_question_en")],
    [InlineKeyboardButton("Изменить финальное сообщение (RU)", callback_data="edit_final_message_ru"),
     InlineKeyboardButton("Edit final message (EN)", callback_data="edit_final_message_en")],
    [InlineKeyboardButton("Закрыть меню", callback_data="close_menu")]
])

# --- Хэндлеры ---

# /start - выбор языка
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {"lang": None, "answers": {}}
    await update.message.reply_text(texts["choose_language"], reply_markup=language_keyboard)
    return LANG_CHOOSE

# Выбор языка
async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    lang = "ru" if "Русский" in text else "en"
    user_data[chat_id]["lang"] = lang
    user_data[chat_id]["answers"] = {}

    # Отправляем первое приветствие и первый вопрос
    await update.message.reply_text(texts[f"welcome_{lang}"], reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text(texts[f"registration_question_{lang}"])

    return ASK_REGISTRATION

# Вопрос о регистрации (второй вопрос)
async def ask_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = user_data[chat_id]["lang"]
    user_data[chat_id]["answers"]["age_country"] = update.message.text

    await update.message.reply_text(texts[f"purpose_question_{lang}"])
    return ASK_PURPOSE

# Вопрос о цели регистрации (третий вопрос)
async def ask_purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = user_data[chat_id]["lang"]
    user_data[chat_id]["answers"]["registration_question"] = update.message.text

    await update.message.reply_text(texts[f"final_message_{lang}"])
    return FINAL_MESSAGE

# Финальное сообщение и завершение
async def final_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data[chat_id]["answers"]["purpose_question"] = update.message.text

    # Можно здесь что-то сделать с собранными ответами, например, логировать или отправить админу

    await update.message.reply_text("✅ Ваши ответы записаны. Спасибо!")
    return ConversationHandler.END

# --- Админ ---

# Команда /settings — меню для редактирования текстов
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(texts["access_denied"])
        return ConversationHandler.END

    await update.message.reply_text(texts["settings_menu_title"], reply_markup=admin_menu_keyboard)
    return ADMIN_MENU

# Обработка нажатий в меню админа
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "close_menu":
        await query.message.delete()
        return ConversationHandler.END

    # Сохраняем ключ редактируемого текста в user_data
    user_data[update.effective_user.id] = {"edit_key": data.replace("edit_", "")}

    await query.message.edit_text(
        texts["edit_prompt"],
        reply_markup=None
    )
    return ADMIN_EDIT_TEXT

# Приём нового текста от админа
async def admin_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(texts["access_denied"])
        return ConversationHandler.END

    new_text = update.message.text
    key = user_data[user_id]["edit_key"]
    texts[key] = new_text
    save_texts(texts)

    await update.message.reply_text(f"✅ Текст '{key}' обновлён.")

    # Показываем меню заново
    await update.message.reply_text(texts["settings_menu_title"], reply_markup=admin_menu_keyboard)
    return ADMIN_MENU

# --- ConversationHandler для опроса ---
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_handler)],
    states={
        LANG_CHOOSE: [MessageHandler(filters.Regex("^(🇷🇺  Русский|🇬🇧  English)$"), language_chosen)],
        ASK_REGISTRATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_registration)],
        ASK_PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_purpose)],
        FINAL_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, final_message)],
        ADMIN_MENU: [CallbackQueryHandler(admin_menu_handler)],
        ADMIN_EDIT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_edit_text)],
    },
    fallbacks=[]
)

# Добавляем обработчик для команды /settings для входа в меню админа
application.add_handler(CommandHandler("settings", settings_command))
application.add_handler(conv_handler)

logger.info("🚀 Bot is starting...")
application.run_polling()



