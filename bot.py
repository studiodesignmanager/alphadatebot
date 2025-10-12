#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
import logging
import os

# --- Настройки ---
BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
ADMIN_ID = 486225736

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- Стейты ---
LANG, GENDER, AGE, COUNTRY, INTERNATIONAL, PURPOSE = range(6)

# --- Тексты ---
WELCOME_TEXT = (
    "👋 Добрый день! Пожалуйста, ответьте на несколько вопросов.\n\n"
    "✍️ Это поможет нам лучше понять вашу цель обращения и быстрее вам помочь.\n\n"
    "👋 Good afternoon! Please answer a few questions.\n\n"
    "✍️ This will help us better understand why you are contacting us and assist you more efficiently."
)

LANGUAGE_BUTTONS = [["РУССКИЙ", "ENGLISH"]]
GENDER_BUTTONS = [["Мужской", "Женский"], ["Male", "Female"]]
YES_NO_BUTTONS = [["Да", "Нет"], ["Yes", "No"]]

FINAL_MESSAGE = (
    "Спасибо за ответы! ❤️\n\n"
    "Нажмите кнопку ниже и отправьте нам сообщение, чтобы мы могли связаться с вами."
)
FINAL_BUTTON = InlineKeyboardMarkup([[InlineKeyboardButton("📩 НАПИСАТЬ НАМ", url="https://t.me/ваш_канал")]])

# --- Хэндлеры ---
def start(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    update.message.reply_text(WELCOME_TEXT, reply_markup=ReplyKeyboardMarkup(LANGUAGE_BUTTONS, one_time_keyboard=True))
    return LANG

def lang(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    user_lang = update.message.text
    context.user_data["lang"] = "RU" if user_lang == "РУССКИЙ" else "EN"
    update.message.reply_text("Выберите ваш пол / Select your gender:", reply_markup=ReplyKeyboardMarkup(GENDER_BUTTONS, one_time_keyboard=True))
    return GENDER

def gender(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    context.user_data["gender"] = update.message.text
    update.message.reply_text("Введите ваш возраст / Enter your age:")
    return AGE

def age(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    context.user_data["age"] = update.message.text
    update.message.reply_text("Введите страну проживания / Enter your country of residence:")
    return COUNTRY

def country(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    context.user_data["country"] = update.message.text
    update.message.reply_text("Были ли у вас регистрации на международных сайтах знакомств ранее? / Have you registered on international dating sites before?", reply_markup=ReplyKeyboardMarkup(YES_NO_BUTTONS, one_time_keyboard=True))
    return INTERNATIONAL

def international(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    context.user_data["international"] = update.message.text
    update.message.reply_text("С какой целью вас интересует регистрация? / What is your purpose for registration?")
    return PURPOSE

def purpose(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    context.user_data["purpose"] = update.message.text

    user = update.message.from_user
    lang = context.user_data.get("lang", "RU")
    msg = (
        f"Username: @{user.username or 'Не указан'}\n"
        f"Имя: {user.first_name}\n"
        f"Язык: {'Русский' if lang=='RU' else 'English'}\n"
        f"Пол: {context.user_data['gender']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Страна: {context.user_data['country']}\n"
        f"Был(а) на международных сайтах: {context.user_data['international']}\n"
        f"Цель регистрации: {context.user_data['purpose']}"
    )
    context.bot.send_message(chat_id=ADMIN_ID, text=msg)
    update.message.reply_text(FINAL_MESSAGE, reply_markup=FINAL_BUTTON)
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    update.message.reply_text("Диалог завершён / Conversation cancelled.")
    return ConversationHandler.END

# --- Main ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, lang)],
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
    import asyncio
    asyncio.run(main())




















