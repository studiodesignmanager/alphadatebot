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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TEXTS_FILE = "texts.json"

CHOOSING_LANGUAGE, ASKING_FIRST_QUESTION, CHOOSING_TEXT, TYPING_NEW_TEXT = range(4)

ADMIN_ID = 486225736  # Твой Telegram ID

def load_texts():
    try:
        with open(TEXTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        default_texts = {
            "ru": {
                "welcome_message": "👋 Добро пожаловать!\n\nЭтот бот поможет вам сделать первый шаг к новым отношениям.\nОтвечайте искренне — это важный шаг навстречу новому знакомству 💖",
                "first_question": "У вас были регистрации на международных сайтах знакомств ранее?"
            },
            "en": {
                "welcome_message": "👋 Welcome!\n\nThis bot will help you take the first step toward a new relationship.\nBe honest — it's an important step toward meaningful connection 💖",
                "first_question": "Have you registered on international dating sites before?"
            }
        }
        with open(TEXTS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_texts, f, ensure_ascii=False, indent=2)
        return default_texts

def save_texts(texts):
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

texts = load_texts()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start from user {update.effective_user.id}")
    reply_keyboard = [["Русский", "English"]]
    await update.message.reply_text(
        "Please choose your language / Пожалуйста, выберите язык:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSING_LANGUAGE

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text.lower()
    logger.info(f"Language chosen: {lang} by user {update.effective_user.id}")
    if lang.startswith("рус"):
        context.user_data["lang"] = "ru"
    elif lang.startswith("eng"):
        context.user_data["lang"] = "en"
    else:
        await update.message.reply_text("Please choose a valid language / Пожалуйста, выберите язык.")
        return CHOOSING_LANGUAGE

    user_lang = context.user_data["lang"]
    user_id = update.effective_user.id

    # Отправляем приветствие и первый вопрос
    await update.message.reply_text(texts[user_lang]["welcome_message"])
    await update.message.reply_text(texts[user_lang]["first_question"])

    # Если админ — добавляем кнопку Настройки
    if user_id == ADMIN_ID:
        buttons = [["Настройки"]]
        await update.message.reply_text(
            "Меню:" if user_lang == "ru" else "Menu:",
            reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True),
        )
    else:
        await update.message.reply_text(
            "Продолжайте, пожалуйста." if user_lang == "ru" else "Please continue.",
            reply_markup=ReplyKeyboardRemove(),
        )

    # Ждём ответ на первый вопрос
    return ASKING_FIRST_QUESTION

async def handle_first_question_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    context.user_data["first_question_answer"] = answer  # Сохраняем ответ

    user_lang = context.user_data.get("lang", "en")

    await update.message.reply_text(
        ("Спасибо за ответ! Если хотите, используйте меню." if user_lang == "ru" else "Thanks for your answer! Use the menu if you want."),
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END

async def edit_texts_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return ConversationHandler.END

    reply_keyboard = [["Приветствие", "Первый вопрос"], ["Отмена"]]
    await update.message.reply_text(
        "Что хотите отредактировать?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSING_TEXT

async def choose_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_choice = update.message.text
    if text_choice == "Отмена":
        await update.message.reply_text("Редактирование отменено.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    context.user_data["edit_choice"] = text_choice
    # Для простоты показываем русские версии. Можно расширить до многоязычия.
    current_value = (
        texts["ru"]["welcome_message"] if text_choice == "Приветствие" else texts["ru"]["first_question"]
    )
    await update.message.reply_text(
        f"Текущий текст для '{text_choice}':\n\n{current_value}\n\nОтправьте новый текст:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return TYPING_NEW_TEXT

async def save_new_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    choice = context.user_data.get("edit_choice")

    if choice == "Приветствие":
        texts["ru"]["welcome_message"] = new_text
    elif choice == "Первый вопрос":
        texts["ru"]["first_question"] = new_text
    else:
        await update.message.reply_text("Произошла ошибка.")
        return ConversationHandler.END

    save_texts(texts)
    await update.message.reply_text(f"Текст '{choice}' обновлён успешно!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def handle_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    return await edit_texts_start(update, context)

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("Error: BOT_TOKEN environment variable is not set!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            ASKING_FIRST_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_first_question_response)],
            CHOOSING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_text)],
            TYPING_NEW_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv_handler)

    # Обработчик для команды "Настройки" от админа вне ConversationHandler
    app.add_handler(MessageHandler(
        filters.Regex("^(Настройки)$") & filters.User(user_id=ADMIN_ID),
        handle_settings_command
    ))

    app.run_polling()

if __name__ == "__main__":
    main()




