import json
import logging
import os

from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_ID = 486225736

LANGUAGE, QUESTION_1, QUESTION_2 = range(3)
SETTINGS_MENU, EDIT_LANGUAGE, EDIT_KEY, EDIT_VALUE = range(3, 7)

with open("texts.json", encoding="utf-8") as f:
    texts = json.load(f)

user_data = {}
edit_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["РУССКИЙ", "ENGLISH"]]
    await update.message.reply_text(
        "Выберите язык / Choose your language:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return LANGUAGE

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = "ru" if "РУССКИЙ" in update.message.text else "en"
    context.user_data["lang"] = lang
    user_data[update.effective_user.id] = {"lang": lang}

    await update.message.reply_text(
        texts[lang]["question_1"],
        reply_markup=ReplyKeyboardRemove()
    )
    return QUESTION_1

async def question_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["q1"] = update.message.text
    lang = user_data[update.effective_user.id]["lang"]

    await notify_admin(update, f"Q1: {update.message.text}")

    await update.message.reply_text(texts[lang]["question_2"])
    return QUESTION_2

async def question_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["q2"] = update.message.text
    lang = user_data[update.effective_user.id]["lang"]

    await notify_admin(update, f"Q2: {update.message.text}")
    await update.message.reply_text(texts[lang]["final"])
    return ConversationHandler.END

async def notify_admin(update: Update, message: str):
    user = update.effective_user
    if user.username:
        user_ref = f"@{user.username}"
    else:
        user_ref = f"[user](tg://user?id={user.id})"
    full_msg = f"{user_ref}:\n{message}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=full_msg, parse_mode="Markdown")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = [
        [InlineKeyboardButton("Редактировать тексты", callback_data="edit_texts")]
    ]
    await update.message.reply_text("Настройки:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SETTINGS_MENU

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "edit_texts":
        keyboard = [
            [InlineKeyboardButton("Русский", callback_data="edit_lang_ru")],
            [InlineKeyboardButton("English", callback_data="edit_lang_en")]
        ]
        await query.edit_message_text("Выберите язык:", reply_markup=InlineKeyboardMarkup(keyboard))
        return EDIT_LANGUAGE

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = "ru" if "ru" in query.data else "en"
    edit_data["lang"] = lang

    keys = list(texts[lang].keys())
    keyboard = [[InlineKeyboardButton(key, callback_data=f"edit_key_{key}")] for key in keys]
    await query.edit_message_text("Выберите текст для редактирования:", reply_markup=InlineKeyboardMarkup(keyboard))
    return EDIT_KEY

async def select_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.split("_", 2)[-1]
    edit_data["key"] = key

    current_value = texts[edit_data["lang"]][key]
    await query.edit_message_text(f"Текущий текст:\n\n{current_value}\n\nОтправьте новый текст:")
    return EDIT_VALUE

async def save_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = edit_data["lang"]
    key = edit_data["key"]
    texts[lang][key] = update.message.text

    with open("texts.json", "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

    await update.message.reply_text("Текст обновлён.")
    return ConversationHandler.END

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Please set BOT_TOKEN environment variable")

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            QUESTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_1)],
            QUESTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_2)],
        },
        fallbacks=[],
    )

    admin_handler = ConversationHandler(
        entry_points=[CommandHandler("admin", admin)],
        states={
            SETTINGS_MENU: [CallbackQueryHandler(settings_menu)],
            EDIT_LANGUAGE: [CallbackQueryHandler(select_language)],
            EDIT_KEY: [CallbackQueryHandler(select_key)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_value)],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)
    application.add_handler(admin_handler)

    logger.info("Bot started")
    application.run_polling()

if __name__ == "__main__":
    main()








