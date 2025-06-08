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

# Состояния разговора
(
    LANG_CHOOSE,
    ASK_AGE_COUNTRY,
    ASK_REGISTRATION,
    ASK_PURPOSE,
    FINAL_MESSAGE,
    ADMIN_MENU,
    ADMIN_EDIT_TEXT,
) = range(7)


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

language_keyboard = ReplyKeyboardMarkup(
    [["🇷🇺 Русский", "🇬🇧 English"]],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выберите язык / Choose language",
)

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


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(texts["choose_language"], reply_markup=language_keyboard)
    context.user_data.clear()
    return LANG_CHOOSE


async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lang = "ru" if "Русский" in text else "en"
    context.user_data["lang"] = lang
    context.user_data["answers"] = {}

    await update.message.reply_text(texts[f"welcome_{lang}"], reply_markup=ReplyKeyboardRemove())
    return ASK_AGE_COUNTRY


async def ask_age_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    context.user_data["answers"]["age_country"] = update.message.text

    await update.message.reply_text(texts[f"registration_question_{lang}"])
    return ASK_REGISTRATION


async def ask_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    context.user_data["answers"]["registration_question"] = update.message.text

    await update.message.reply_text(texts[f"purpose_question_{lang}"])
    return ASK_PURPOSE


async def ask_purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    context.user_data["answers"]["purpose_question"] = update.message.text

    await update.message.reply_text(texts[f"final_message_{lang}"])
    return FINAL_MESSAGE


async def final_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answers"]["final_message_received"] = update.message.text

    # Отправим все ответы админу
    answer_text = "\n".join(f"{k}: {v}" for k, v in context.user_data["answers"].items())
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Новый опрос от @{update.effective_user.username or update.effective_user.id}:\n{answer_text}"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки ответов админу: {e}")

    await update.message.reply_text("✅ Ваши ответы записаны. Спасибо!")
    return ConversationHandler.END


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(texts["access_denied"])
        return ConversationHandler.END

    await update.message.reply_text(texts["settings_menu_title"], reply_markup=admin_menu_keyboard)
    return ADMIN_MENU


async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "close_menu":
        await query.message.delete()
        return ConversationHandler.END

    context.user_data["edit_key"] = data.replace("edit_", "")
    await query.message.edit_text(texts["edit_prompt"])
    return ADMIN_EDIT_TEXT


async def admin_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(texts["access_denied"])
        return ConversationHandler.END

    new_text = update.message.text
    key = context.user_data.get("edit_key")
    if key:
        texts[key] = new_text
        save_texts(texts)
        await update.message.reply_text(f"✅ Текст '{key}' обновлён.")
    else:
        await update.message.reply_text("❌ Ошибка: ключ для редактирования не найден.")

    await update.message.reply_text(texts["settings_menu_title"], reply_markup=admin_menu_keyboard)
    return ADMIN_MENU


conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_handler)],
    states={
        LANG_CHOOSE: [MessageHandler(filters.Regex("^(🇷🇺 Русский|🇬🇧 English)$"), language_chosen)],
        ASK_AGE_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age_country)],
        ASK_REGISTRATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_registration)],
        ASK_PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_purpose)],
        FINAL_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, final_message)],
        ADMIN_MENU: [CallbackQueryHandler(admin_menu_handler)],
        ADMIN_EDIT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_edit_text)],
    },
    fallbacks=[]
)

application.add_handler(CommandHandler("settings", settings_command))
application.add_handler(conv_handler)

if __name__ == "__main__":
    print("✅ Бот запускается...")
    logger.info("🚀 Bot is starting...")
    application.run_polling()





