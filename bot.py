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
BOT_TOKEN = "7110528714:AAG0mSUIkaEsbsJBL4FeCIq461HI2-xqx0g"

LANG, Q1, Q2, FINAL, ADMIN_MENU, EDIT_LANG, EDIT_TEXT = range(7)

def load_texts():
    try:
        with open("texts.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info("Successfully loaded texts.json")
            return data
    except FileNotFoundError:
        logger.error("texts.json not found, using default texts")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in texts.json: {e}, using default texts")
    except Exception as e:
        logger.error(f"Unexpected error loading texts.json: {e}, using default texts")
    return {
        "ru": {
            "greeting": "Добрый день! Ответьте, пожалуйста, на несколько вопросов.",
            "question_1": "У вас были регистрации на международных сайтах знакомствах ранее?",
            "question_2": "С какой целью интересует регистрация?",
            "final": "Спасибо! Мы свяжемся с вами в ближайшее время"
        },
        "en": {
            "greeting": "Good afternoon! Please answer a few questions.",
            "question_1": "Have you registered on any international dating sites before?",
            "question_2": "What is your reason for signing up?",
            "final": "Thank you! We will get in touch with you shortly."
        }
    }

def save_texts(texts):
    try:
        with open("texts.json", "w", encoding="utf-8") as f:
            json.dump(texts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving texts.json: {e}")

texts = load_texts()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    buttons = [["РУССКИЙ", "ENGLISH"]]
    if user_id == ADMIN_ID:
        buttons[0].append("Настройки")
    reply_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        f"{texts['ru']['greeting']}\n\n{texts['en']['greeting']}",
        reply_markup=reply_markup
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
        context.user_data["lang"] = "ru"
    elif choice in ["english", "en"]:
        context.user_data["lang"] = "en"
    else:
        await update.message.reply_text("Пожалуйста, выберите язык кнопкой.")
        return LANG
    await update.message.reply_text(texts[context.user_data["lang"]]["question_1"], reply_markup=ReplyKeyboardRemove())
    return Q1

async def q1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q1"] = update.message.text
    await update.message.reply_text(texts[context.user_data["lang"]]["question_2"])
    return Q2

async def q2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q2"] = update.message.text
    lang = context.user_data["lang"]
    
    await update.message.reply_text(texts[lang]["final"])

    if lang == "ru":
        btn_text = "📩 НАПИСАТЬ НАМ"
        btn_label = "Если у вас есть дополнительные вопросы, нажмите кнопку ниже:"
    else:
        btn_text = "📩 CONTACT US"
        btn_label = "If you have additional questions, click the button below:"

    keyboard = [[InlineKeyboardButton(btn_text, url="https://t.me/ВАШ_ЮЗЕРНЕЙМ")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(btn_label, reply_markup=reply_markup)

    username = update.effective_user.username
    user_id = update.effective_user.id
    link = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"
    admin_msg = (
        f"Ответы пользователя @{username if username else '[нет username]'} (id: {user_id}):\n"
        f"Язык: {lang}\n"
        f"Вопрос 1: {context.user_data['q1']}\n"
        f"Вопрос 2: {context.user_data['q2']}\n"
        f"Ссылка: {link}"
    )
    try:
        await context.bot.send_message(ADMIN_ID, admin_msg)
    except Exception as e:
        logger.error(f"Error sending message to admin: {e}")
    return ConversationHandler.END

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.lower()
    if choice == "назад":
        buttons = [["РУССКИЙ", "ENGLISH"]]
        buttons[0].append("Настройки")
        await update.message.reply_text("Выберите язык / Select language:", reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
        return LANG
    if choice in ["ru", "русский"]:
        context.user_data["edit_lang"] = "ru"
    elif choice in ["en", "english"]:
        context.user_data["edit_lang"] = "en"
    else:
        await update.message.reply_text("Пожалуйста, выберите язык кнопкой.")
        return ADMIN_MENU

    buttons = [["greeting", "question_1", "question_2", "final"], ["Назад"]]
    await update.message.reply_text(
        f"Выберите текст для редактирования ({context.user_data['edit_lang']}):",
        reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
    )
    return EDIT_LANG

async def edit_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.lower()
    if choice == "назад":
        await update.message.reply_text(
            "Админка: Выберите язык для редактирования:",
            reply_markup=ReplyKeyboardMarkup([["RU", "EN"], ["Назад"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return ADMIN_MENU
    if choice not in ["greeting", "question_1", "question_2", "final"]:
        await update.message.reply_text("Пожалуйста, выберите кнопку.")
        return EDIT_LANG
    context.user_data["edit_text_key"] = choice
    await update.message.reply_text("Введите новый текст:")
    return EDIT_TEXT

async def edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    lang = context.user_data["edit_lang"]
    key = context.user_data["edit_text_key"]
    texts[lang][key] = new_text
    save_texts(texts)
    await update.message.reply_text(f"Текст для {key} ({lang}) обновлён.")
    await update.message.reply_text(
        "Админка: Выберите язык для редактирования:",
        reply_markup=ReplyKeyboardMarkup([["RU", "EN"], ["Назад"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return ADMIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    logger.info("Starting bot...")
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, q1)],
            Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, q2)],
            ADMIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_menu)],
            EDIT_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_lang)],
            EDIT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    application.add_handler(conv_handler)
    logger.info("Bot handlers initialized, starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main()

















