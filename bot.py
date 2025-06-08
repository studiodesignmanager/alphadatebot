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

(
    CHOOSING_TEXT,
    TYPING_NEW_TEXT,
    WAITING_FOR_ANSWER_1,
    WAITING_FOR_ANSWER_2,
    WAITING_FOR_ANSWER_3,
) = range(5)

def load_texts():
    try:
        with open(TEXTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        default_texts = {
            "welcome_message": "Добро пожаловать!",
            "first_question": "У вас были регистрации на международных сайтах знакомств ранее?",
            "second_question": "Какой у вас опыт в онлайн-знакомствах?",
            "third_question": "Что вы ищете на нашем сервисе?",
            "thank_you": "Спасибо за ваши ответы! Мы свяжемся с вами в ближайшее время."
        }
        with open(TEXTS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_texts, f, ensure_ascii=False, indent=2)
        return default_texts

def save_texts(texts):
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

texts = load_texts()

ADMIN_ID = 123456789  # <-- Вставь сюда свой Telegram ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(texts["welcome_message"])
    await update.message.reply_text(texts["first_question"])
    return WAITING_FOR_ANSWER_1

async def answer_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer_1"] = update.message.text
    await update.message.reply_text(texts["second_question"])
    return WAITING_FOR_ANSWER_2

async def answer_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer_2"] = update.message.text
    await update.message.reply_text(texts["third_question"])
    return WAITING_FOR_ANSWER_3

async def answer_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer_3"] = update.message.text
    await update.message.reply_text(texts["thank_you"])
    # Здесь можно обработать ответы или сохранить куда-то
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
    current_value = (
        texts["welcome_message"] if text_choice == "Приветствие" else texts["first_question"]
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
        texts["welcome_message"] = new_text
    elif choice == "Первый вопрос":
        texts["first_question"] = new_text
    else:
        await update.message.reply_text("Произошла ошибка.")
        return ConversationHandler.END

    save_texts(texts)
    await update.message.reply_text(f"Текст '{choice}' обновлён успешно!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("Error: BOT_TOKEN environment variable is not set!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler_edit_texts = ConversationHandler(
        entry_points=[CommandHandler("edit_texts", edit_texts_start)],
        states={
            CHOOSING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_text)],
            TYPING_NEW_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    conv_handler_dialog = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_ANSWER_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_1)],
            WAITING_FOR_ANSWER_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_2)],
            WAITING_FOR_ANSWER_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_3)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv_handler_edit_texts)
    app.add_handler(conv_handler_dialog)

    app.run_polling()

if __name__ == "__main__":
    main()



