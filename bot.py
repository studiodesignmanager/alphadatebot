from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
import logging

# -------------------- Логирование --------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------- Переменные --------------------
BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
ADMIN_ID = 486225736

# Состояния ConversationHandler
LANG, GENDER, AGE, COUNTRY, REGISTERED, PURPOSE = range(6)

# -------------------- Тексты --------------------
welcome_text = (
    "👋 Добрый день! Пожалуйста, ответьте на несколько вопросов.\n\n"
    "✍️ Это поможет нам лучше понять вашу цель обращения и быстрее вам помочь.\n\n"
    "👋 Good afternoon! Please answer a few questions.\n\n"
    "✍️ This will help us better understand why you are contacting us and assist you more efficiently."
)

language_keyboard = [["РУССКИЙ", "ENGLISH"]]

gender_keyboard_ru = [["Мужской", "Женский"]]
gender_keyboard_en = [["Male", "Female"]]

final_text = (
    "Спасибо за ответы! ❤️\n\n"
    "Нажмите кнопку ниже и отправьте нам сообщение, чтобы мы могли связаться с вами."
)

# -------------------- Хендлеры --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(language_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return LANG

async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = update.message.text
    context.user_data["lang"] = "RU" if user_lang == "РУССКИЙ" else "EN"
    
    # Пол
    keyboard = gender_keyboard_ru if context.user_data["lang"] == "RU" else gender_keyboard_en
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    text = "Выберите пол:" if context.user_data["lang"] == "RU" else "Select your gender:"
    await update.message.reply_text(text, reply_markup=reply_markup)
    return GENDER

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text
    text = "Введите ваш возраст:" if context.user_data["lang"] == "RU" else "Enter your age:"
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    text = "Введите вашу страну проживания:" if context.user_data["lang"] == "RU" else "Enter your country of residence:"
    await update.message.reply_text(text)
    return COUNTRY

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text
    text = "Были ли вы на международных сайтах знакомств ранее? (Да/Нет)" if context.user_data["lang"] == "RU" else "Have you been registered on international dating sites before? (Yes/No)"
    await update.message.reply_text(text)
    return REGISTERED

async def registered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["registered"] = update.message.text
    text = "С какой целью вас интересует регистрация?" if context.user_data["lang"] == "RU" else "What is your purpose for registration?"
    await update.message.reply_text(text)
    return PURPOSE

async def purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["purpose"] = update.message.text

    # Отправка админу
    lang = "Русский" if context.user_data["lang"] == "RU" else "English"
    message = (
        f"Username: @{update.effective_user.username}\n"
        f"Имя: {update.effective_user.full_name}\n"
        f"Язык: {lang}\n"
        f"Пол: {context.user_data['gender']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Страна: {context.user_data['country']}\n"
        f"Был(а) на международных сайтах: {context.user_data['registered']}\n"
        f"Цель регистрации: {context.user_data['purpose']}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)

    # Финальное сообщение с кнопкой
    keyboard = [[InlineKeyboardButton("📩 НАПИСАТЬ НАМ", url="https://t.me/alphadate")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(final_text, reply_markup=reply_markup)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вы отменили заполнение анкеты.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# -------------------- Основная функция --------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, lang)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country)],
            REGISTERED: [MessageHandler(filters.TEXT & ~filters.COMMAND, registered)],
            PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, purpose)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()

















