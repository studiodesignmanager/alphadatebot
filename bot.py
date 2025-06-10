import json
import logging
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Уровни состояний
LANGUAGE, QUESTION_1, QUESTION_2 = range(3)

# Админ ID
ADMIN_ID = 486225736

# Загрузка текстов
with open("texts.json", "r", encoding="utf-8") as f:
    texts = json.load(f)

# Временное хранилище данных пользователя
user_data = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_keyboard = [[KeyboardButton("РУССКИЙ")], [KeyboardButton("ENGLISH")]]

    if user_id == ADMIN_ID:
        lang_keyboard.append([KeyboardButton("Настройки")])

    await update.message.reply_text(
        "Выберите язык / Choose your language:",
        reply_markup=ReplyKeyboardMarkup(lang_keyboard, resize_keyboard=True),
    )
    return LANGUAGE


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text
    lang_key = "ru" if lang == "РУССКИЙ" else "en"
    context.user_data["lang"] = lang_key
    await update.message.reply_text(
        texts[lang_key]["question_1"], reply_markup=ReplyKeyboardRemove()
    )
    return QUESTION_1


async def question_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    context.user_data["answer_1"] = answer

    # Отправить админу сразу
    user = update.effective_user
    username = user.username
    contact_info = f"@{username}" if username else f"https://t.me/user?id={user.id}"
    lang_key = context.user_data["lang"]
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"{contact_info}\n\n{texts[lang_key]['question_1']}\n{answer}",
    )

    await update.message.reply_text(texts[lang_key]["question_2"])
    return QUESTION_2


async def question_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    context.user_data["answer_2"] = answer

    # Отправить админу сразу
    user = update.effective_user
    username = user.username
    contact_info = f"@{username}" if username else f"https://t.me/user?id={user.id}"
    lang_key = context.user_data["lang"]
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"{contact_info}\n\n{texts[lang_key]['question_2']}\n{answer}",
    )

    await update.message.reply_text(texts[lang_key]["final"])
    return ConversationHandler.END


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    langs = list(texts.keys())
    reply = "🛠 Настройки:\n\n"
    for lang in langs:
        reply += f"<b>{lang.upper()}</b>:\n"
        for key, value in texts[lang].items():
            reply += f"<b>{key}</b>: {value}\n"
        reply += "\n"

    await update.message.reply_text(reply, parse_mode="HTML")


def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            QUESTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_1)],
            QUESTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_2)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Настройки$"), settings))

    app.run_polling()


if __name__ == "__main__":
    main()










