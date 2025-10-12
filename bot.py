#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
import logging
import json

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен
BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
ADMIN_ID = 486225736

# Состояния ConversationHandler
LANG, GENDER, AGE, COUNTRY, INTERNATIONAL, PURPOSE, FINISH = range(7)

# Приветствие
def start(update: Update, context: CallbackContext) -> int:
    greeting = (
        "👋 Добрый день! Пожалуйста, ответьте на несколько вопросов.\n\n"
        "✍️ Это поможет нам лучше понять вашу цель обращения и быстрее вам помочь.\n\n"
        "👋 Good afternoon! Please answer a few questions.\n\n"
        "✍️ This will help us better understand why you are contacting us and assist you more efficiently."
    )

    keyboard = [
        [KeyboardButton("РУССКИЙ"), KeyboardButton("ENGLISH")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(greeting, reply_markup=reply_markup)
    return LANG

# Выбор языка
def choose_language(update: Update, context: CallbackContext) -> int:
    lang = update.message.text
    context.user_data['lang'] = lang
    if lang == "РУССКИЙ":
        keyboard = [[KeyboardButton("Мужчина"), KeyboardButton("Женщина")]]
        update.message.reply_text("Пожалуйста, выберите ваш пол:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    else:
        keyboard = [[KeyboardButton("Man"), KeyboardButton("Woman")]]
        update.message.reply_text("Please select your gender:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return GENDER

# Выбор пола
def choose_gender(update: Update, context: CallbackContext) -> int:
    context.user_data['gender'] = update.message.text
    lang = context.user_data.get('lang', 'РУССКИЙ')
    if lang == "РУССКИЙ":
        update.message.reply_text("Сколько вам полных лет?")
    else:
        update.message.reply_text("How old are you?")
    return AGE

# Ввод возраста
def age(update: Update, context: CallbackContext) -> int:
    context.user_data['age'] = update.message.text
    lang = context.user_data.get('lang', 'РУССКИЙ')
    if lang == "РУССКИЙ":
        update.message.reply_text("В какой стране вы проживаете постоянно?")
    else:
        update.message.reply_text("In which country do you permanently reside?")
    return COUNTRY

# Ввод страны
def country(update: Update, context: CallbackContext) -> int:
    context.user_data['country'] = update.message.text
    lang = context.user_data.get('lang', 'РУССКИЙ')
    if lang == "РУССКИЙ":
        keyboard = [[KeyboardButton("Да"), KeyboardButton("Нет")]]
        update.message.reply_text(
            "У вас были регистрации на международных сайтах знакомств ранее?",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
    else:
        keyboard = [[KeyboardButton("Yes"), KeyboardButton("No")]]
        update.message.reply_text(
            "Have you registered on international dating sites before?",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
    return INTERNATIONAL

# Международные сайты
def international(update: Update, context: CallbackContext) -> int:
    context.user_data['international'] = update.message.text
    lang = context.user_data.get('lang', 'РУССКИЙ')
    if lang == "РУССКИЙ":
        update.message.reply_text("С какой целью интересует регистрация?")
    else:
        update.message.reply_text("What is your purpose for registering?")
    return PURPOSE

# Цель регистрации
def purpose(update: Update, context: CallbackContext) -> int:
    context.user_data['purpose'] = update.message.text

    user_data = context.user_data
    username = update.message.from_user.username or ""
    first_name = update.message.from_user.first_name or ""
    lang = user_data.get('lang', 'РУССКИЙ')

    msg = (
        f"Username: @{username}\n"
        f"Имя: {first_name}\n"
        f"Язык: {lang}\n"
        f"Пол: {user_data.get('gender', '')}\n"
        f"Возраст: {user_data.get('age', '')}\n"
        f"Страна: {user_data.get('country', '')}\n"
        f"Был(а) на международных сайтах: {user_data.get('international', '')}\n"
        f"Цель регистрации: {user_data.get('purpose', '')}"
    )

    context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    final_msg = (
        "Спасибо за ответы! ❤️\n\n"
        "Нажмите кнопку ниже и отправьте нам сообщение, чтобы мы могли связаться с вами."
    )
    keyboard = [[KeyboardButton("📩 НАПИСАТЬ НАМ")]]
    update.message.reply_text(final_msg, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return FINISH

# Конец
def finish(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Мы получили ваше сообщение и свяжемся с вами в ближайшее время!")
    return ConversationHandler.END

# Команда /cancel
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Опрос отменён.")
    return ConversationHandler.END

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
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
















