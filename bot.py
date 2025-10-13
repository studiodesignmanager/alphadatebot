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
    ConversationHandler,
    ContextTypes,
)
from pytz import timezone

# 🔹 Настройки
TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
ADMIN_ID = 486225736

# 🔹 Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🔹 Состояния
LANG, GENDER, AGE, COUNTRY, INTERNATIONAL, PURPOSE, FINISH = range(7)


# 🔹 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["РУССКИЙ", "ENGLISH"]]
    await update.message.reply_text(
        "Выберите язык / Choose your language:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return LANG


# 🔹 Выбор языка
async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text
    context.user_data["lang"] = "ru" if "РУССКИЙ" in lang else "en"

    if context.user_data["lang"] == "ru":
        text = (
            "Добрый день! Ответьте, пожалуйста, на несколько вопросов.\n\n"
            "Это поможет нам лучше узнать цель вашего обращения и помочь вам быстрее."
        )
        keyboard = [["Мужчина", "Женщина"]]
    else:
        text = (
            "Good afternoon! Please answer a few questions.\n\n"
            "This will help us better understand your purpose for contacting us and assist you."
        )
        keyboard = [["Man", "Woman"]]

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return GENDER


# 🔹 Пол
async def choose_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text
    lang = context.user_data["lang"]

    text = "Сколько вам полных лет?" if lang == "ru" else "How old are you?"
    await update.message.reply_text(text)
    return AGE


# 🔹 Возраст
async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    lang = context.user_data["lang"]

    text = (
        "В какой стране вы проживаете постоянно?"
        if lang == "ru"
        else "Which country do you permanently live in?"
    )
    await update.message.reply_text(text)
    return COUNTRY


# 🔹 Страна
async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text
    lang = context.user_data["lang"]

    text = (
        "У вас были регистрации на международных сайтах знакомств ранее?"
        if lang == "ru"
        else "Have you registered on international dating sites before?"
    )
    await update.message.reply_text(text)
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


# 🔹 Цель регистрации
async def purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["purpose"] = update.message.text
    lang = context.user_data["lang"]

    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.first_name
    answers = context.user_data

    # 🔹 Отправляем админу все ответы
    message_to_admin = (
        f"📩 Новый ответ от {username}\n\n"
        f"Пол: {answers.get('gender')}\n"
        f"Возраст: {answers.get('age')}\n"
        f"Страна: {answers.get('country')}\n"
        f"Регистрация ранее: {answers.get('international')}\n"
        f"Цель: {answers.get('purpose')}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=message_to_admin)

    # 🔹 Финал пользователю
    if lang == "ru":
        text = "Спасибо! Мы свяжемся с вами в ближайшее время ❤️"
        button = InlineKeyboardButton("📩📩 НАПИСАТЬ НАМ", url="https://t.me/alphadate")
    else:
        text = "Thank you! We will get in touch with you shortly ❤️"
        button = InlineKeyboardButton("📩📩 CONTACT US", url="https://t.me/alphadate")

    keyboard = InlineKeyboardMarkup([[button]])
    await update.message.reply_text(text, reply_markup=keyboard)

    # 🔹 очищаем данные, чтобы можно было пройти снова
    context.user_data.clear()

    return ConversationHandler.END


# 🔹 /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён. Для перезапуска напишите /start.")
    context.user_data.clear()
    return ConversationHandler.END


# 🔹 Основная функция
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country)],
            INTERNATIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, international)],
            PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, purpose)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,  # 🔥 позволяет одному пользователю запустить /start снова
    )

    app.add_handler(conv_handler)

    print("✅ Bot started successfully!")
    app.run_polling()


if __name__ == "__main__":
    main()


























