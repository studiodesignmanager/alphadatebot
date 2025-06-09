import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from dotenv import load_dotenv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TEXTS_FILE = "texts.json"

# Conversation states
CHOOSING_LANGUAGE, ASKING_FIRST_QUESTION, ASKING_SECOND_QUESTION, CHOOSING_TEXT, TYPING_NEW_TEXT = range(5)

ADMIN_ID = 486225736  # overwritten by .env


def load_texts():
    try:
        with open(TEXTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        default_texts = {
            "ru": {
                "welcome_message": "👋 Добро пожаловать!",
                "first_question": "У вас были регистрации на международных сайтах знакомств ранее?",
                "second_question": "С какой целью интересует регистрация?",
                "thank_you": "Спасибо! Мы свяжемся с вами в ближайшее время."
            },
            "en": {
                "welcome_message": "👋 Welcome!",
                "first_question": "Have you registered on international dating sites before?",
                "second_question": "What is your reason for signing up?",
                "thank_you": "Thank you! We will get in touch with you shortly."
            }
        }
        save_texts(default_texts)
        return default_texts


def save_texts(texts):
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)


texts = load_texts()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start from user {update.effective_user.id}")
    reply_keyboard = [["РУССКИЙ", "ENGLISH"]]
    await update.message.reply_text(
        "Please choose your language / Пожалуйста, выберите язык:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSING_LANGUAGE


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text.startswith("рус"):
        context.user_data["lang"] = "ru"
    elif text.startswith("eng"):
        context.user_data["lang"] = "en"
    else:
        await update.message.reply_text(
            "Please choose a valid language / Пожалуйста, выберите язык."
        )
        return CHOOSING_LANGUAGE

    user_lang = context.user_data["lang"]
    logger.info(f"User {update.effective_user.id} selected language: {user_lang}")

    # Send welcome + first question
    await update.message.reply_text(texts[user_lang]["welcome_message"])
    await update.message.reply_text(
        texts[user_lang]["first_question"],
        reply_markup=ReplyKeyboardRemove()
    )
    await update.message.reply_text(
        "(Пожалуйста, введите ответ ниже)" if user_lang == "ru" else "(Please type your answer below)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASKING_FIRST_QUESTION


async def handle_first_question_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["first_answer"] = update.message.text.strip()
    user_lang = context.user_data.get("lang", "en")

    # Send second question
    await update.message.reply_text(texts[user_lang]["second_question"])
    await update.message.reply_text(
        "(Пожалуйста, введите ответ ниже)" if user_lang == "ru" else "(Please type your answer below)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASKING_SECOND_QUESTION


async def handle_second_question_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["second_answer"] = update.message.text.strip()
    user_lang = context.user_data.get("lang", "en")
    user_id = update.effective_user.id

    # Thank you
    await update.message.reply_text(texts[user_lang]["thank_you"], reply_markup=ReplyKeyboardRemove())

    # Admin settings button
    if user_id == ADMIN_ID:
        buttons = [["Настройки"]] if user_lang == "ru" else [["Settings"]]
        await update.message.reply_text(
            "Меню:" if user_lang == "ru" else "Menu:",
            reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
        )

    return ConversationHandler.END


async def handle_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return ConversationHandler.END
    return await edit_texts_start(update, context)


async def edit_texts_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["welcome_message", "first_question"], ["second_question", "thank_you"], ["Cancel"]]
    await update.message.reply_text(
        "Что хотите отредактировать?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_TEXT


async def choose_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if choice.lower() == "cancel":
        await update.message.reply_text("Редактирование отменено.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    if choice not in ["welcome_message", "first_question", "second_question", "thank_you"]:
        await update.message.reply_text("Пожалуйста, выберите из предложенных вариантов или 'Cancel'.")
        return CHOOSING_TEXT

    context.user_data["edit_key"] = choice
    context.user_data["editing_lang"] = "ru"
    await update.message.reply_text(
        f"Текущий текст [RU] для '{choice}':\n{texts['ru'][choice]}\n\nОтправьте новый текст:",
        reply_markup=ReplyKeyboardRemove()
    )
    return TYPING_NEW_TEXT


async def save_new_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = context.user_data.get("edit_key")
    lang = context.user_data.get("editing_lang")
    new = update.message.text.strip()
    texts[lang][key] = new
    save_texts(texts)

    if lang == "ru":
        context.user_data["editing_lang"] = "en"
        await update.message.reply_text(
            f"Теперь отправьте текст [EN] для '{key}':\n{texts['en'][key]}"
        )
        return TYPING_NEW_TEXT
    else:
        await update.message.reply_text("Текст обновлён для обоих языков!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("Error: BOT_TOKEN environment variable is not set!")
    global ADMIN_ID
    ADMIN_ID = int(os.getenv("ADMIN_ID", str(ADMIN_ID)))

    app = ApplicationBuilder().token(bot_token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            ASKING_FIRST_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_first_question_response)],
            ASKING_SECOND_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_second_question_response)],
            CHOOSING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_text)],
            TYPING_NEW_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^(Настройки|Settings)$") & filters.User(user_id=ADMIN_ID), handle_settings_command))

    logger.info("Bot started polling...")
    app.run_polling()


if __name__ == "__main__":
    main()



