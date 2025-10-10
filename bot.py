import json
import logging
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 486225736
BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"

# Состояния
LANG, ASK_GENDER, ASK_AGE, ASK_COUNTRY, Q1, Q2, FINAL = range(7)

# Загрузка текстов
def load_texts():
    with open("texts.json", "r", encoding="utf-8") as f:
        return json.load(f)

texts = load_texts()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [["РУССКИЙ", "ENGLISH"]]
    reply_markup = ReplyKeyboardRemove()
    await update.message.reply_text(
        f"{texts['ru']['greeting']}\n\n{texts['en']['greeting']}",
        reply_markup=reply_markup
    )
    return LANG

# Выбор языка
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.lower()
    if choice in ["русский", "ru"]:
        context.user_data["lang"] = "ru"
    elif choice in ["english", "en"]:
        context.user_data["lang"] = "en"
    else:
        await update.message.reply_text("Пожалуйста, выберите язык кнопкой.")
        return LANG

    lang = context.user_data["lang"]
    # После выбора языка спрашиваем пол
    keyboard = [
        [InlineKeyboardButton(texts[lang]["gender_male"], callback_data="male")],
        [InlineKeyboardButton(texts[lang]["gender_female"], callback_data="female")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(texts[lang]["gender_question"], reply_markup=reply_markup)
    return ASK_GENDER

# Пол
async def gender_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["gender"] = query.data
    lang = context.user_data["lang"]
    await query.message.reply_text(texts[lang]["age_question"])
    return ASK_AGE

# Возраст
async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["country_question"])
    return ASK_COUNTRY

# Страна
async def ask_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["question_1"])
    return Q1

# Вопрос 1
async def q1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q1"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["question_2"])
    return Q2

# Вопрос 2
async def q2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q2"] = update.message.text
    lang = context.user_data["lang"]

    await update.message.reply_text(texts[lang]["final"])

    # Кнопка контакта
    contact_text = texts[lang]["contact_button"]
    keyboard = [[InlineKeyboardButton(contact_text, url="https://t.me/alphadate")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(texts[lang]["contact_prompt"], reply_markup=reply_markup)

    # Отправка админу
    username = update.effective_user.username
    user_id = update.effective_user.id
    link = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"
    admin_msg = (
        f"Ответы пользователя @{username if username else '[нет username]'} (id: {user_id}):\n"
        f"Пол: {context.user_data['gender']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Страна: {context.user_data['country']}\n"
        f"Вопрос 1: {context.user_data['q1']}\n"
        f"Вопрос 2: {context.user_data['q2']}\n"
        f"Ссылка: {link}"
    )
    await context.bot.send_message(ADMIN_ID, admin_msg)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена.")
    return ConversationHandler.END

# Запуск
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            ASK_GENDER: [CallbackQueryHandler(gender_chosen)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            ASK_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_country)],
            Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, q1)],
            Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, q2)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()













