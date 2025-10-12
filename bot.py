#!/usr/bin/env python3
# coding: utf-8

import json
import os
import logging
from dotenv import load_dotenv

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# ---------- Настройка ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Попробуем загрузить из .env, если есть
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or ""
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)

# Если хотите — можно вписать токен/админ id прямо здесь (не рекомендуется для публичных репозиториев)
# TOKEN = "7110...ВАШ_ТОКЕН..."
# ADMIN_ID = 486225736

if not TOKEN or not ADMIN_ID:
    raise RuntimeError("⛔ Установите TELEGRAM_TOKEN и ADMIN_ID в .env или в коде.")

TEXTS_FILE = "texts.json"

# ---------- Conversation states ----------
(
    STATE_LANG_CHOOSE,
    STATE_GENDER,
    STATE_AGE,
    STATE_COUNTRY,
    STATE_REGISTERED,
    STATE_PURPOSE,
    STATE_FINAL,
) = range(7)

# ---------- Загрузка текстов (texts.json) ----------
def load_texts():
    if not os.path.exists(TEXTS_FILE):
        # Дефолтные тексты (на случай отсутствия файла)
        return {
            "ru": {
                "greeting": "👋 Добрый день! Пожалуйста, ответьте на несколько вопросов.\n\n✍️ Это поможет нам лучше понять вашу цель обращения и быстрее вам помочь.",
                "choose_language_prompt": "Пожалуйста, выберите язык:",
                "gender_question": "Выберите ваш пол:",
                "gender_male": "Мужской",
                "gender_female": "Женский",
                "age_question": "Пожалуйста, укажите ваш возраст:",
                "country_question": "Пожалуйста, укажите вашу страну проживания:",
                "registered_question": "У вас были регистрации на международных сайтах знакомств ранее?",
                "registered_yes": "Да",
                "registered_no": "Нет",
                "purpose_question": "С какой целью интересует регистрация?",
                "final_message": "Спасибо за ответы! ❤️\n\nНажмите кнопку ниже и отправьте нам сообщение, чтобы мы могли связаться с вами.",
                "contact_button": "📩 НАПИСАТЬ НАМ",
                "contact_prompt": "Если у вас есть дополнительные вопросы, нажмите кнопку ниже:",
            },
            "en": {
                "greeting": "👋 Good afternoon! Please answer a few questions.\n\n✍️ This will help us better understand why you are contacting us and assist you more efficiently.",
                "choose_language_prompt": "Please select a language:",
                "gender_question": "Select your gender:",
                "gender_male": "Male",
                "gender_female": "Female",
                "age_question": "Please enter your age:",
                "country_question": "Please enter your country of residence:",
                "registered_question": "Have you been registered on international dating sites before?",
                "registered_yes": "Yes",
                "registered_no": "No",
                "purpose_question": "What is the purpose of your registration?",
                "final_message": "Thank you for your answers! ❤️\n\nPress the button below and send us a message so we can contact you.",
                "contact_button": "📩 CONTACT US",
                "contact_prompt": "If you have additional questions, click the button below:",
            },
        }
    with open(TEXTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


texts = load_texts()

# ---------- Хелперы ----------
def lang_label(lang):
    return "ru" if lang == "ru" else "en"


# ---------- Хендлеры ----------

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start — отправляет приветствие (RU + EN) и клавиатуру выбора языка.
    Приветствие — в одном сообщении, затем сообщение с кнопками.
    """
    # Отправляем строго тот текст, который вы просили — сначала оба приветствия в полном виде.
    greeting_ru = texts["ru"]["greeting"]
    greeting_en = texts["en"]["greeting"]

    # Отправляем приветствие (оба языка)
    await update.message.reply_text(f"{greeting_ru}\n\n{greeting_en}")

    # Затем показываем prompt с кнопками языка
    keyboard = [["🇷🇺 Русский", "🇬🇧 English"]]
    reply = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Выберите язык / Choose language")
    await update.message.reply_text(texts["ru"].get("choose_language_prompt", "Пожалуйста, выберите язык:") + " / " + texts["en"].get("choose_language_prompt", "Please select a language:"), reply_markup=reply)

    return STATE_LANG_CHOOSE


async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # Определяем язык по тексту кнопки
    if "рус" in text.lower() or text.startswith("🇷🇺"):
        lang = "ru"
    else:
        lang = "en"
    context.user_data["lang"] = lang
    context.user_data["answers"] = {}

    # Сразу спрашиваем пол с inline-кнопками (локализованные)
    kb = [
        [
            InlineKeyboardButton(texts[lang]["gender_male"], callback_data="gender_male"),
            InlineKeyboardButton(texts[lang]["gender_female"], callback_data="gender_female"),
        ]
    ]
    await update.message.reply_text(texts[lang]["gender_question"], reply_markup=InlineKeyboardMarkup(kb))
    return STATE_GENDER


async def gender_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = context.user_data.get("lang", "ru")
    # Сохраняем пол
    if data == "gender_male":
        context.user_data["answers"]["gender"] = texts[lang]["gender_male"]
    else:
        context.user_data["answers"]["gender"] = texts[lang]["gender_female"]

    # Задаём вопрос про возраст (текстом)
    await query.message.reply_text(texts[lang]["age_question"], reply_markup=ReplyKeyboardRemove())
    return STATE_AGE


async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answers"]["age"] = update.message.text.strip()
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(texts[lang]["country_question"])
    return STATE_COUNTRY


async def ask_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answers"]["country"] = update.message.text.strip()
    lang = context.user_data.get("lang", "ru")

    # После страны — спрашиваем про регистрации на международных сайтах с клавиатурой (да/нет)
    yes = texts[lang].get("registered_yes", "Да" if lang == "ru" else "Yes")
    no = texts[lang].get("registered_no", "Нет" if lang == "ru" else "No")
    keyboard = [[yes, no]]
    await update.message.reply_text(texts[lang]["registered_question"], reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return STATE_REGISTERED


async def ask_registered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ответ "Да" или "Нет" (или localized)
    answer = update.message.text.strip()
    lang = context.user_data.get("lang", "ru")
    # Нормализуем to yes/no
    context.user_data["answers"]["registered"] = answer

    # Далее — цель регистрации (текст)
    await update.message.reply_text(texts[lang]["purpose_question"], reply_markup=ReplyKeyboardRemove())
    return STATE_PURPOSE


async def ask_purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answers"]["purpose"] = update.message.text.strip()
    lang = context.user_data.get("lang", "ru")

    # Финальное сообщение пользователю
    await update.message.reply_text(texts[lang]["final_message"])

    # Кнопка контакта (с вашей ссылкой @alphadate)
    contact_label = texts[lang].get("contact_button", "📩 НАПИСАТЬ НАМ")
    contact_prompt = texts[lang].get("contact_prompt", "")
    kb = [[InlineKeyboardButton(contact_label, url="https://t.me/alphadate")]]
    await update.message.reply_text(contact_prompt, reply_markup=InlineKeyboardMarkup(kb))

    # Отправка админу в нужном формате
    user = update.effective_user
    username = user.username if user.username else "[нет username]"
    user_link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

    answers = context.user_data["answers"]
    admin_text = (
        f"Username: @{username}\n"
        f"Имя: {user.first_name or ''} {user.last_name or ''}\n"
        f"Язык: {'Русский' if lang == 'ru' else 'English'}\n"
        f"Пол: {answers.get('gender','')}\n"
        f"Возраст: {answers.get('age','')}\n"
        f"Страна: {answers.get('country','')}\n"
        f"Был(а) на международных сайтах: {answers.get('registered','')}\n"
        f"Цель регистрации: {answers.get('purpose','')}\n"
        f"Ссылка: {user_link}"
    )

    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception as e:
        logger.error("Ошибка отправки админу: %s", e)

    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ---------- Роутинг / старт приложения ----------
def build_application():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            STATE_LANG_CHOOSE: [MessageHandler(filters.Regex("^(🇷🇺 Русский|🇷🇺  Русский|🇷🇺|Русский|🇬🇧 English|English|ENGLISH)$"), language_chosen)],
            STATE_GENDER: [CallbackQueryHandler(gender_chosen)],
            STATE_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            STATE_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_country)],
            STATE_REGISTERED: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_registered)],
            STATE_PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_purpose)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        allow_reentry=True,
        per_user=True,
    )

    app.add_handler(conv)
    return app


def main():
    app = build_application()
    logger.info("🚀 Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
















