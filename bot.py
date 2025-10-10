import json
import logging
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 486225736
BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"

# Состояния
LANG, GENDER, AGE, COUNTRY, Q1, Q2, FINAL, ADMIN_MENU, EDIT_LANG, EDIT_TEXT = range(10)


def load_texts():
    try:
        with open("texts.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.warning("texts.json not found or invalid, using defaults")
        return {
            "ru": {
                "greeting": "Добрый день! Ответьте, пожалуйста, на несколько вопросов.\n\nЭто поможет нам лучше узнать цель вашего обращения и помочь вам.",
                "gender": "Выберите ваш пол:",
                "gender_buttons": ["Мужчина", "Женщина"],
                "age": "Напишите, пожалуйста, ваш полный возраст:",
                "country": "Из какой вы страны?",
                "question_1": "У вас были регистрации на международных сайтах знакомств ранее?",
                "question_2": "С какой целью интересует регистрация?",
                "final": "Спасибо! Мы свяжемся с вами в ближайшее время.",
                "contact_prompt": "Если у вас есть дополнительные вопросы, нажмите кнопку ниже:"
            },
            "en": {
                "greeting": "Good afternoon! Please answer a few questions.\n\nThis will help us better understand your purpose for contacting us and assist you.",
                "gender": "Please select your gender:",
                "gender_buttons": ["Man", "Woman"],
                "age": "Please write your full age:",
                "country": "Which country do you live in permanently?",
                "question_1": "Have you registered on international dating sites before?",
                "question_2": "What is your reason for signing up?",
                "final": "Thank you! We will contact you shortly.",
                "contact_prompt": "If you have additional questions, click the button below:"
            }
        }


def save_texts(texts):
    with open("texts.json", "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)


texts = load_texts()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    buttons = [["РУССКИЙ", "ENGLISH"]]
    if user_id == ADMIN_ID:
        buttons[0].append("Настройки")
    await update.message.reply_text(
        f"{texts['ru']['greeting']}\n\n{texts['en']['greeting']}",
        reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
    )
    return LANG


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.lower()
    if choice == "настройки" and update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(
            "Админка: Выберите язык для редактирования:",
            reply_markup=ReplyKeyboardMarkup([["RU", "EN"], ["Назад"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return ADMIN_MENU
    if choice in ["русский", "ru"]:
        lang = "ru"
    elif choice in ["english", "en"]:
        lang = "en"
    else:
        await update.message.reply_text("Пожалуйста, выберите язык кнопкой.")
        return LANG

    context.user_data["lang"] = lang
    gender_buttons = texts[lang]["gender_buttons"]
    await update.message.reply_text(
        texts[lang]["gender"],
        reply_markup=ReplyKeyboardMarkup([gender_buttons], one_time_keyboard=True, resize_keyboard=True)
    )
    return GENDER


async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["age"], reply_markup=ReplyKeyboardRemove())
    return AGE


async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["country"])
    return COUNTRY


async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["question_1"])
    return Q1


async def q1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q1"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["question_2"])
    return Q2


async def q2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q2"] = update.message.text
    lang = context.user_data["lang"]

    await update.message.reply_text(texts[lang]["final"])

    btn_text = "📩 НАПИСАТЬ НАМ" if lang == "ru" else "📩 CONTACT US"
    keyboard = [[InlineKeyboardButton(btn_text, url="https://t.me/alphadate")]]
    await update.message.reply_text(
        texts[lang]["contact_prompt"], reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # Отправка админу
    username = update.effective_user.username
    user_id = update.effective_user.id
    link = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"

    msg = (
        f"Ответы пользователя @{username if username else '[нет username]'} (id: {user_id}):\n"
        f"Язык: {lang}\n"
        f"Пол: {context.user_data['gender']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Страна: {context.user_data['country']}\n"
        f"Вопрос 1: {context.user_data['q1']}\n"
        f"Вопрос 2: {context.user_data['q2']}\n"
        f"Ссылка: {link}"
    )
    try:
        await context.bot.send_message(ADMIN_ID, msg)
    except Exception as e:
        logger.error(f"Ошибка при отправке админу: {e}")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country)],
            Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, q1)],
            Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, q2)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()



















