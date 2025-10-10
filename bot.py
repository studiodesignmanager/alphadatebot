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

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 486225736
BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"

# Состояния разговора
(
    LANG_CHOOSE,
    ASK_GENDER,
    ASK_AGE,
    ASK_COUNTRY,
    ASK_REGISTRATION,
    ASK_PURPOSE,
    FINAL_MESSAGE,
    ADMIN_MENU,
    EDIT_LANG,
    EDIT_TEXT,
) = range(10)

# Тексты
def load_texts():
    try:
        with open("texts.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info("Successfully loaded texts.json")
            return data
    except Exception as e:
        logger.error(f"Error loading texts.json: {e}")
        # Дефолтные тексты
        return {
            "ru": {
                "greeting": "Добрый день! Ответьте, пожалуйста, на несколько вопросов.\n\nЭто поможет нам лучше узнать цель вашего обращения и помочь вам.",
                "gender": "Укажите ваш пол:",
                "age": "Укажите, пожалуйста, ваш возраст:",
                "country": "Укажите вашу страну проживания:",
                "question_1": "У вас были регистрации на международных сайтах знакомств ранее?",
                "question_2": "С какой целью интересует регистрация?",
                "final": "Спасибо! Мы свяжемся с вами в ближайшее время",
                "contact_btn": "📩 НАПИСАТЬ НАМ"
            },
            "en": {
                "greeting": "Good afternoon! Please answer a few questions.\n\nThis will help us better understand your purpose for contacting us and assist you.",
                "gender": "Select your gender:",
                "age": "Please enter your age:",
                "country": "Please enter your country of residence:",
                "question_1": "Have you registered on any international dating sites before?",
                "question_2": "What is your reason for signing up?",
                "final": "Thank you! We will get in touch with you shortly.",
                "contact_btn": "📩 CONTACT US"
            }
        }

def save_texts(texts):
    try:
        with open("texts.json", "w", encoding="utf-8") as f:
            json.dump(texts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving texts.json: {e}")

texts = load_texts()

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Приветствие
    reply_markup = ReplyKeyboardMarkup(
        [["РУССКИЙ", "ENGLISH"]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text(
        f"{texts['ru']['greeting']}\n\n{texts['en']['greeting']}",
        reply_markup=reply_markup
    )
    context.user_data.clear()
    return LANG_CHOOSE

# Выбор языка
async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "русский" in text or text == "ru":
        context.user_data["lang"] = "ru"
    elif "english" in text or text == "en":
        context.user_data["lang"] = "en"
    else:
        await update.message.reply_text("Пожалуйста, выберите язык кнопкой.")
        return LANG_CHOOSE

    # Переходим к выбору пола
    lang = context.user_data["lang"]
    gender_buttons = [["Мужчина", "Женщина"]] if lang == "ru" else [["Male", "Female"]]
    await update.message.reply_text(texts[lang]["gender"], reply_markup=ReplyKeyboardMarkup(gender_buttons, one_time_keyboard=True, resize_keyboard=True))
    return ASK_GENDER

# Пол
async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["age"], reply_markup=ReplyKeyboardRemove())
    return ASK_AGE

# Возраст
async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["country"])
    return ASK_COUNTRY

# Страна
async def ask_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["question_1"])
    return ASK_REGISTRATION

# Вопрос 1
async def ask_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["question_1"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["question_2"])
    return ASK_PURPOSE

# Вопрос 2
async def ask_purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["question_2"] = update.message.text
    lang = context.user_data["lang"]

    # Финальное сообщение
    await update.message.reply_text(texts[lang]["final"])

    # Кнопка контакта
    keyboard = [[InlineKeyboardButton(texts[lang]["contact_btn"], url="https://t.me/alphadate")]]
    await update.message.reply_text("Если хотите связаться:", reply_markup=InlineKeyboardMarkup(keyboard))

    # Отправка админу
    username = update.effective_user.username
    user_id = update.effective_user.id
    link = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"
    admin_msg = (
        f"Новый пользователь @{username if username else '[нет username]'} (id: {user_id}):\n"
        f"Пол: {context.user_data['gender']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Страна: {context.user_data['country']}\n"
        f"Регистрации: {context.user_data['question_1']}\n"
        f"Цель: {context.user_data['question_2']}\n"
        f"Ссылка: {link}"
    )
    try:
        await context.bot.send_message(ADMIN_ID, admin_msg)
    except Exception as e:
        logger.error(f"Error sending message to admin: {e}")
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Main
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_chosen)],
            ASK_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gender)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            ASK_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_country)],
            ASK_REGISTRATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_registration)],
            ASK_PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_purpose)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    logger.info("Bot started, polling...")
    application.run_polling()

if __name__ == "__main__":
    main()












