import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
ADMIN_ID = 486225736

LANG, GENDER, AGE, COUNTRY, INTERNATIONAL, PURPOSE, FINISH = range(7)

# ================ ОБРАБОТЧИКИ ================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    greeting = (
        "👋 Добрый день! Пожалуйста, ответьте на несколько вопросов.\n\n"
        "✍️ Это поможет нам лучше понять вашу цель обращения и быстрее вам помочь.\n\n"
        "👋 Good afternoon! Please answer a few questions.\n\n"
        "✍️ This will help us better understand why you are contacting us and assist you more efficiently."
    )
    keyboard = [[KeyboardButton("РУССКИЙ"), KeyboardButton("ENGLISH")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(greeting, reply_markup=reply_markup)
    return LANG

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = update.message.text
    context.user_data['lang'] = lang
    if lang == "РУССКИЙ":
        keyboard = [[KeyboardButton("Мужчина"), KeyboardButton("Женщина")]]
        await update.message.reply_text(
            "Пожалуйста, выберите ваш пол:", 
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
    else:
        keyboard = [[KeyboardButton("Man"), KeyboardButton("Woman")]]
        await update.message.reply_text(
            "Please select your gender:", 
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
    return GENDER

async def choose_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['gender'] = update.message.text
    lang = context.user_data['lang']
    if lang == "РУССКИЙ":
        await update.message.reply_text("Сколько вам полных лет?")
    else:
        await update.message.reply_text("How old are you?")
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['age'] = update.message.text
    lang = context.user_data['lang']
    if lang == "РУССКИЙ":
        await update.message.reply_text("Пожалуйста, укажите вашу страну проживания")
    else:
        await update.message.reply_text("Please indicate your country of residence")
    return COUNTRY

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['country'] = update.message.text
    lang = context.user_data['lang']
    if lang == "РУССКИЙ":
        keyboard = [[KeyboardButton("Да"), KeyboardButton("Нет")]]
        await update.message.reply_text(
            "У вас были регистрации на международных сайтах знакомств ранее?",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
    else:
        keyboard = [[KeyboardButton("Yes"), KeyboardButton("No")]]
        await update.message.reply_text(
            "Have you registered on international dating sites before?",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
    return INTERNATIONAL

async def international(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['international'] = update.message.text
    lang = context.user_data['lang']
    if lang == "РУССКИЙ":
        await update.message.reply_text("С какой целью интересует регистрация?")
    else:
        await update.message.reply_text("What is your purpose for registering?")
    return PURPOSE

async def purpose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['purpose'] = update.message.text

    user = update.message.from_user
    lang = context.user_data['lang']

    # Отправляем админу
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

    # Финальное сообщение пользователю
    lang = context.user_data['lang']
    if lang == "РУССКИЙ":
        final_text = (
            "Спасибо за ответы! ❤️\n\n"
            "Нажмите кнопку ниже и отправьте нам сообщение, чтобы мы могли связаться с вами."
        )
        final_keyboard = [[KeyboardButton("📩 НАПИСАТЬ НАМ")]]
    else:
        final_text = (
            "Thank you for your answers! ❤️\n\n"
            "Click the button below and send us a message so we can get in touch with you."
        )
        final_keyboard = [[KeyboardButton("📩 CONTACT US")]]
    
    await update.message.reply_text(final_text, reply_markup=ReplyKeyboardMarkup(final_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return FINISH

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Открываем чат сразу
    chat_url = "https://t.me/alphadate"
    await update.message.reply_text(chat_url)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Опрос отменен.")
    return ConversationHandler.END

# ================ MAIN ================

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
        allow_reentry=True  # Позволяет пользователю пройти опрос повторно
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()




























