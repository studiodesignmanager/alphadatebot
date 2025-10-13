import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# 🔹 Включаем логирование
logging.basicConfig(level=logging.INFO)

# 🔹 Константы состояний
LANGUAGE, GENDER, AGE, COUNTRY, INTERNATIONAL, PURPOSE = range(6)

# 🔹 Токен и админ ID
TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
ADMIN_ID = 486225736


# 🔹 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # позволяет проходить заново
    keyboard = [["РУССКИЙ", "ENGLISH"]]

    await update.message.reply_text(
        "🌍 Please select your language / Пожалуйста, выберите язык:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return LANGUAGE


# 🔹 Выбор языка
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text
    context.user_data["lang"] = "ru" if lang == "РУССКИЙ" else "en"

    if lang == "РУССКИЙ":
        text = (
            "👋 Добрый день!\n\n"
            "💬 Это поможет нам лучше узнать цель вашего обращения и помочь вам быстрее.\n\n"
            "Выберите, пожалуйста, свой пол:"
        )
        keyboard = [["Мужчина", "Женщина"]]
    else:
        text = (
            "👋 Good afternoon!\n\n"
            "💬 This will help us better understand your purpose for contacting us and assist you faster.\n\n"
            "Please select your gender:"
        )
        keyboard = [["Man", "Woman"]]

    await update.message.reply_text(
        text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return GENDER


# 🔹 Пол
async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text
    lang = context.user_data["lang"]

    text = "Сколько вам полных лет?" if lang == "ru" else "How old are you?"
    await update.message.reply_text(text)
    return AGE


# 🔹 Возраст
async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    lang = context.user_data["lang"]

    text = "В какой стране вы проживаете постоянно?" if lang == "ru" else "Which country do you live in permanently?"
    await update.message.reply_text(text)
    return COUNTRY


# 🔹 Страна
async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text
    lang = context.user_data["lang"]

    if lang == "ru":
        text = "У вас были регистрации на международных сайтах знакомств ранее?"
        keyboard = [["Да", "Нет"]]
    else:
        text = "Have you registered on international dating sites before?"
        keyboard = [["Yes", "No"]]

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return INTERNATIONAL


# 🔹 Международные регистрации
async def international(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["international"] = update.message.text
    lang = context.user_data["lang"]

    text = (
        "С какой целью интересует регистрация?"
        if lang == "ru"
        else "What is your purpose for registration?"
    )
    await update.message.reply_text(text)
    return PURPOSE


# 🔹 Цель регистрации + финал
async def purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["purpose"] = update.message.text
    lang = context.user_data["lang"]
    user = update.effective_user
    data = context.user_data

    # 🔸 Отправка админу
    msg_admin = (
        f"📩 Новый ответ от @{user.username or 'без username'} (ID: {user.id})\n\n"
        f"Пол: {data.get('gender')}\n"
        f"Возраст: {data.get('age')}\n"
        f"Страна: {data.get('country')}\n"
        f"Регистрация ранее: {data.get('international')}\n"
        f"Цель: {data.get('purpose')}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin)

    # 🔸 Финальное сообщение
    if lang == "ru":
        text = (
            "❤️ Спасибо за ваши ответы!\n\n"
            "Нажмите кнопку ниже, чтобы написать нам прямо сейчас 👇"
        )
        keyboard = [[KeyboardButton("📩 НАПИСАТЬ НАМ", url="https://t.me/alphadate")]]
    else:
        text = (
            "❤️ Thank you for your answers!\n\n"
            "Click the button below to contact us directly 👇"
        )
        keyboard = [[KeyboardButton("📩 CONTACT US", url="https://t.me/alphadate")]]

    await update.message.reply_text(
        text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return ConversationHandler.END


# 🔹 Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён. Чтобы начать заново, введите /start")
    return ConversationHandler.END


# 🔹 Основной запуск
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country)],
            INTERNATIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, international)],
            PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, purpose)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()



























