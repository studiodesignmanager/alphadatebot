import os
import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Логи
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Админ ID (замени на свой Telegram ID)
ADMIN_ID = 486225736

# Состояния
CHOOSING_LANG, ASKED_PREV_REG, ASKED_PURPOSE = range(3)

# Клавиатуры
lang_keyboard = [["Русский", "English"]]

# Тексты на двух языках
texts = {
    "Русский": {
        "welcome": "Добро пожаловать!",
        "question1": "У вас были регистрации на международных сайтах знакомств ранее?",
        "question2": "С какой целью интересует регистрация?",
        "thank": "Спасибо! Мы свяжемся с вами в ближайшее время.",
    },
    "English": {
        "welcome": "Welcome!",
        "question1": "Have you ever registered on international dating sites before?",
        "question2": "What is your purpose for registration?",
        "thank": "Thank you! We will contact you soon.",
    },
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, выберите язык / Please choose a language:",
        reply_markup=ReplyKeyboardMarkup(lang_keyboard, one_time_keyboard=True),
    )
    return CHOOSING_LANG


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text
    if lang not in texts:
        await update.message.reply_text(
            "Пожалуйста, выберите язык из списка / Please choose from the list."
        )
        return CHOOSING_LANG

    context.user_data["lang"] = lang

    # Приветствие + первый вопрос
    await update.message.reply_text(
        texts[lang]["welcome"] + "\n" + texts[lang]["question1"],
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASKED_PREV_REG


async def prev_registration_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "Русский")
    user = update.effective_user

    # Отправляем админу с юзернеймом и ответом
    answer = update.message.text
    admin_msg = (
        f"Ответ пользователя @{user.username or user.first_name}:\n"
        f"Вопрос: {texts[lang]['question1']}\nОтвет: {answer}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)

    # Задаём второй вопрос
    await update.message.reply_text(texts[lang]["question2"])
    return ASKED_PURPOSE


async def purpose_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "Русский")
    user = update.effective_user

    answer = update.message.text
    admin_msg = (
        f"Ответ пользователя @{user.username or user.first_name}:\n"
        f"Вопрос: {texts[lang]['question2']}\nОтвет: {answer}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)

    # Благодарим и завершаем
    await update.message.reply_text(texts[lang]["thank"])
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Действие отменено.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("Error: BOT_TOKEN environment variable is not set!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            ASKED_PREV_REG: [MessageHandler(filters.TEXT & ~filters.COMMAND, prev_registration_answer)],
            ASKED_PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, purpose_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()


