import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ======== ЛОГИ ========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
ADMIN_ID = 486225736

LANG, GENDER, AGE, COUNTRY, INTERNATIONAL, PURPOSE, FINISH = range(7)

# ======== НАБОР ТЕКСТОВ (встроен, без JSON-файла) ========
TEXTS = {
    "РУССКИЙ": {
        "start": "👋 Добрый день! Пожалуйста, ответьте на несколько вопросов.\n\n✍️ Это поможет нам лучше понять вашу цель обращения и быстрее вам помочь.",
        "gender": "Пожалуйста, выберите ваш пол:",
        "age": "Сколько вам полных лет?",
        "country": "Пожалуйста, укажите вашу страну проживания",
        "international": "У вас были регистрации на международных сайтах знакомств ранее?",
        "purpose": "С какой целью интересует регистрация?",
        "final": "Спасибо за ответы! ❤️\n\nНажмите кнопку ниже и отправьте нам сообщение, чтобы мы могли связаться с вами",
        "button": "📩 НАПИСАТЬ НАМ"
    },
    "ENGLISH": {
        "start": "👋 Good afternoon! Please answer a few questions.\n\n✍️ This will help us better understand why you are contacting us and assist you more efficiently.",
        "gender": "Please select your gender:",
        "age": "How old are you?",
        "country": "Please indicate your country of residence",
        "international": "Have you registered on international dating sites before?",
        "purpose": "What is your purpose for registering?",
        "final": "Thank you for your answers! ❤️\n\nClick the button below and send us a message so we can get in touch with you.",
        "button": "📩 CONTACT US"
    }
}

# ======== ОБРАБОТЧИКИ ========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[KeyboardButton("РУССКИЙ"), KeyboardButton("ENGLISH")]]
    await update.message.reply_text(
        "👋 Добрый день / Good afternoon!\n\nВыберите язык / Choose language:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return LANG

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = update.message.text
    if lang not in TEXTS:
        await update.message.reply_text("Пожалуйста, выберите язык из предложенных.")
        return LANG
    context.user_data['lang'] = lang
    texts = TEXTS[lang]
    keyboard = [[KeyboardButton("Мужчина"), KeyboardButton("Женщина")]] if lang == "РУССКИЙ" else [[KeyboardButton("Man"), KeyboardButton("Woman")]]
    await update.message.reply_text(texts["gender"], reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return GENDER

async def choose_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['gender'] = update.message.text
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS[lang]["age"])
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['age'] = update.message.text
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS[lang]["country"])
    return COUNTRY

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['country'] = update.message.text
    lang = context.user_data['lang']
    keyboard = [[KeyboardButton("Да"), KeyboardButton("Нет")]] if lang == "РУССКИЙ" else [[KeyboardButton("Yes"), KeyboardButton("No")]]
    await update.message.reply_text(TEXTS[lang]["international"], reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return INTERNATIONAL

async def international(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['international'] = update.message.text
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS[lang]["purpose"])
    return PURPOSE

async def purpose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['purpose'] = update.message.text
    user = update.message.from_user
    lang = context.user_data['lang']

    text = (
        f"Username: @{user.username if user.username else '-'}\n"
        f"Имя: {user.first_name}\n"
        f"Язык: {lang}\n"
        f"Пол: {context.user_data['gender']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Страна: {context.user_data['country']}\n"
        f"Был(а) на международных сайтах: {context.user_data['international']}\n"
        f"Цель регистрации: {context.user_data['purpose']}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=text)

    keyboard = [[KeyboardButton(TEXTS[lang]["button"], web_app=WebAppInfo(url="https://t.me/alphadate"))]]
    await update.message.reply_text(TEXTS[lang]["final"], reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return FINISH

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Опрос отменен.")
    return ConversationHandler.END

# ======== MAIN ========
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country)],
            INTERNATIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, international)],
            PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, purpose)],
            FINISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()





















