from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
import json
import logging

# ----------------- Конфигурация -----------------
BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
ADMIN_ID = 486225736

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Состояния ConversationHandler
LANGUAGE, GENDER, AGE, COUNTRY, QUESTION1, QUESTION2, FINAL = range(7)

# Загрузка текстов
with open("texts.json", "r", encoding="utf-8") as f:
    TEXTS = json.load(f)

# ----------------- Хендлеры -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["РУССКИЙ", "ENGLISH"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    greeting = (
        "Добрый день! Ответьте, пожалуйста, на несколько вопросов.\n\n"
        "Это поможет нам лучше узнать цель вашего обращения и помочь вам.\n\n"
        "Good afternoon! Please answer a few questions.\n\n"
        "This will help us better understand your purpose for contacting us and assist you."
    )
    await update.message.reply_text(greeting, reply_markup=markup)
    return LANGUAGE

async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text.lower()
    if "рус" in lang:
        context.user_data['lang'] = "ru"
    else:
        context.user_data['lang'] = "en"

    texts = TEXTS[context.user_data['lang']]

    # Кнопки пола
    keyboard = [[texts["gender_male"], texts["gender_female"]]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(texts["gender_question"], reply_markup=markup)
    return GENDER

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['gender'] = update.message.text
    texts = TEXTS[context.user_data['lang']]

    await update.message.reply_text(texts["age_question"], reply_markup=ReplyKeyboardRemove())
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    texts = TEXTS[context.user_data['lang']]

    await update.message.reply_text(texts["country_question"])
    return COUNTRY

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['country'] = update.message.text
    texts = TEXTS[context.user_data['lang']]

    # Кнопки вопроса 1
    keyboard = [["Да", "Нет"]] if context.user_data['lang'] == "ru" else [["Yes", "No"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(texts["question_1"], reply_markup=markup)
    return QUESTION1

async def question1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['question1'] = update.message.text
    texts = TEXTS[context.user_data['lang']]

    await update.message.reply_text(texts["question_2"], reply_markup=ReplyKeyboardRemove())
    return QUESTION2

async def question2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['question2'] = update.message.text
    texts = TEXTS[context.user_data['lang']]

    await update.message.reply_text(texts["final"], reply_markup=ReplyKeyboardRemove())

    # Отправка админу
    user = update.message.from_user
    msg = (
        f"Новый пользователь заполнил анкету:\n"
        f"Username: @{user.username}\n"
        f"Имя: {user.full_name}\n"
        f"Язык: {context.user_data['lang']}\n"
        f"Пол: {context.user_data['gender']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Страна: {context.user_data['country']}\n"
        f"Вопрос 1: {context.user_data['question1']}\n"
        f"Вопрос 2: {context.user_data['question2']}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Опрос отменен.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ----------------- Основная функция -----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_choice)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country)],
            QUESTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question1)],
            QUESTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question2)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()















