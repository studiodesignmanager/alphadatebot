import json
import logging
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

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
    except Exception as e:
        logger.error(f"Error loading texts.json: {e}")
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

    keyboard = [
        [
            InlineKeyboardButton("РУССКИЙ", callback_data="lang_ru"),
            InlineKeyboardButton("ENGLISH", callback_data="lang_en")
        ]
    ]
    if user_id == ADMIN_ID:
        keyboard[0].append(InlineKeyboardButton("Настройки", callback_data="admin_menu"))

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"{texts['ru']['greeting']}\n\n{texts['en']['greeting']}",
        reply_markup=reply_markup
    )
    return LANG

async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "lang_ru":
        context.user_data["lang"] = "ru"
        await query.message.edit_reply_markup(reply_markup=None)
        await query.message.reply_text(texts["ru"]["question_1"], reply_markup=ReplyKeyboardRemove())
        return Q1

    elif data == "lang_en":
        context.user_data["lang"] = "en"
        await query.message.edit_reply_markup(reply_markup=None)
        await query.message.reply_text(texts["en"]["question_1"], reply_markup=ReplyKeyboardRemove())
        return Q1

    elif data == "admin_menu" and user_id == ADMIN_ID:
        buttons = [["RU", "EN"], ["Назад"]]
        await query.message.edit_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "Админка: Выберите язык для редактирования:",
            reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
        )
        return ADMIN_MENU

    await query.message.reply_text("Неверный выбор.")
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
    await update.message.reply_text(texts[context.user_data["lang"]]["final"])
    username = update.effective_user.username
    user_id = update.effective_user.id
    link = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"
    admin_msg = (
        f"Ответы пользователя @{username if username else '[нет username]'} (id: {user_id}):\n"
        f"Язык: {context.user_data['lang']}\n"
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
        if update.effective_user.id == ADMIN_ID:
            buttons[0].append("Настройки")
        await update.message.reply_text(
            "Выберите язык / Select language:",
            reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
        )
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
    try:
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, language), CallbackQueryHandler(handle_inline_buttons)],
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
        application.add_handler(CallbackQueryHandler(handle_inline_buttons))
        application.run_polling()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()













