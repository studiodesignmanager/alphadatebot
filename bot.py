import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

logging.basicConfig(level=logging.INFO)

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ADMIN_ID = 486225736

# Этапы диалога
LANGUAGE, GENDER, AGE, COUNTRY, EXPERIENCE, PURPOSE, FINAL = range(7)

# Тексты
TEXTS = {
    "ru": {
        "start": "Добрый день! Ответьте, пожалуйста, на несколько вопросов.\n\nЭто поможет нам лучше узнать цель вашего обращения и помочь вам быстрее.",
        "choose_gender": "Ваш пол:",
        "gender_buttons": [["Мужчина"], ["Женщина"]],
        "age": "Сколько вам полных лет?",
        "country": "В какой стране вы проживаете постоянно?",
        "experience": "У вас были регистрации на международных сайтах знакомств ранее?",
        "purpose": "С какой целью интересует регистрация?",
        "final": "Спасибо! Мы свяжемся с вами в ближайшее время.",
        "contact_button": "📩 СВЯЗАТЬСЯ"
    },
    "en": {
        "start": "Good afternoon! Please answer a few questions.\n\nThis will help us better understand your purpose for contacting us and assist you.",
        "choose_gender": "Your gender:",
        "gender_buttons": [["Man"], ["Woman"]],
        "age": "How old are you?",
        "country": "What country do you permanently reside in?",
        "experience": "Have you ever registered on international dating sites before?",
        "purpose": "What is your purpose for registration?",
        "final": "Thank you! We will get in touch with you shortly.",
        "contact_button": "📩 CONTACT US"
    }
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["РУССКИЙ", "ENGLISH"]]
    await update.message.reply_text(
        "Выберите язык / Choose your language:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return LANGUAGE


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if "рус" in text:
        context.user_data["lang"] = "ru"
    elif "eng" in text:
        context.user_data["lang"] = "en"
    else:
        await update.message.reply_text("Пожалуйста, выберите язык кнопкой ниже / Please choose a language using the button below.")
        return LANGUAGE

    lang = context.user_data["lang"]
    await update.message.reply_text(TEXTS[lang]["start"])
    await update.message.reply_text(
        TEXTS[lang]["choose_gender"],
        reply_markup=ReplyKeyboardMarkup(TEXTS[lang]["gender_buttons"], resize_keyboard=True, one_time_keyboard=True)
    )
    return GENDER


async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(TEXTS[lang]["age"], reply_markup=None)
    return AGE


async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(TEXTS[lang]["country"])
    return COUNTRY


async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(TEXTS[lang]["experience"])
    return EXPERIENCE


async def experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["experience"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(TEXTS[lang]["purpose"])
    return PURPOSE


async def purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["purpose"] = update.message.text
    lang = context.user_data["lang"]

    data = context.user_data
    user = update.effective_user

    # Отправка админу
    msg = (
        f"📩 Новый ответ от @{user.username or user.first_name} ({user.id})\n\n"
        f"Язык: {lang}\n"
        f"Пол: {data.get('gender')}\n"
        f"Возраст: {data.get('age')}\n"
        f"Страна: {data.get('country')}\n"
        f"Опыт: {data.get('experience')}\n"
        f"Цель: {data.get('purpose')}"
    )
    await context.bot.send_message(ADMIN_ID, msg)

    # Кнопка для связи
    button = InlineKeyboardButton(
        text=TEXTS[lang]["contact_button"],
        url="https://t.me/alphadate"  # Сразу открывает чат
    )
    markup = InlineKeyboardMarkup([[button]])

    await update.message.reply_text(TEXTS[lang]["final"], reply_markup=markup)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён.")
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, experience)],
            PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, purpose)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()






















