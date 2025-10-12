from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters
)
import json
import logging

# Логи
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Состояния
LANG, GENDER, AGE, COUNTRY, Q1, Q2, FINAL = range(7)

# Загрузка текстов
texts = {
    "ru": {
        "greeting": "👋 Добрый день! Пожалуйста, ответьте на несколько вопросов.\n✍️ Это поможет нам лучше понять вашу цель обращения и быстрее вам помочь.\n\nGood afternoon! Please answer a few questions.\n✍️ This will help us better understand why you are contacting us and assist you more efficiently.",
        "gender_question": "Выберите ваш пол:",
        "gender_male": "Мужской",
        "gender_female": "Женский",
        "age_question": "Пожалуйста, укажите ваш возраст:",
        "country_question": "Пожалуйста, укажите вашу страну проживания:",
        "question_1": "У вас были регистрации на международных сайтах знакомств ранее?",
        "question_2": "С какой целью интересует регистрация?",
        "final": "Спасибо! Мы свяжемся с вами в ближайшее время",
        "contact_prompt": "Если у вас есть дополнительные вопросы, нажмите кнопку ниже:",
        "contact_button": "📩 НАПИСАТЬ НАМ"
    },
    "en": {
        "greeting": "👋 Добрый день! Пожалуйста, ответьте на несколько вопросов.\n✍️ Это поможет нам лучше понять вашу цель обращения и быстрее вам помочь.\n\nGood afternoon! Please answer a few questions.\n✍️ This will help us better understand why you are contacting us and assist you more efficiently.",
        "gender_question": "Select your gender:",
        "gender_male": "Male",
        "gender_female": "Female",
        "age_question": "Please enter your age:",
        "country_question": "Please enter your country of residence:",
        "question_1": "Have you registered on any international dating sites before?",
        "question_2": "What is your reason for signing up?",
        "final": "Thank you! We will get in touch with you shortly.",
        "contact_prompt": "If you have additional questions, click the button below:",
        "contact_button": "📩 CONTACT US"
    }
}

user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("РУССКИЙ", callback_data='ru'),
         InlineKeyboardButton("ENGLISH", callback_data='en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(texts['ru']['greeting'], reply_markup=reply_markup)
    return LANG

async def lang_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data['lang'] = lang
    text = texts[lang]['gender_question']
    keyboard = [
        [InlineKeyboardButton(texts[lang]['gender_male'], callback_data='male'),
         InlineKeyboardButton(texts[lang]['gender_female'], callback_data='female')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return GENDER

async def gender_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['gender'] = query.data
    lang = context.user_data['lang']
    await query.edit_message_text(text=texts[lang]['age_question'])
    return AGE

async def age_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    lang = context.user_data['lang']
    await update.message.reply_text(texts[lang]['country_question'])
    return COUNTRY

async def country_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['country'] = update.message.text
    lang = context.user_data['lang']
    await update.message.reply_text(texts[lang]['question_1'])
    return Q1

async def question1_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['q1'] = update.message.text
    lang = context.user_data['lang']
    await update.message.reply_text(texts[lang]['question_2'])
    return Q2

async def question2_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['q2'] = update.message.text
    lang = context.user_data['lang']
    await update.message.reply_text(texts[lang]['final'])
    
    # Здесь можно отправить данные админу
    logging.info(f"New submission: {context.user_data}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Conversation canceled.")
    return ConversationHandler.END

def main():
    BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANG: [CallbackQueryHandler(lang_choice)],
            GENDER: [CallbackQueryHandler(gender_choice)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age_input)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country_input)],
            Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question1_input)],
            Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question2_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__':
    main()
















