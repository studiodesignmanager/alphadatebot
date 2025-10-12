import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# ID администратора
ADMIN_ID = 486225736

# Состояния
LANG, GENDER, AGE, COUNTRY, EXPERIENCE, PURPOSE = range(6)

# Хранение данных пользователя
user_data_temp = {}

# Приветствие с выбором языка
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [
            InlineKeyboardButton("РУССКИЙ", callback_data='RU'),
            InlineKeyboardButton("ENGLISH", callback_data='EN')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Добрый день! Пожалуйста, ответьте на несколько вопросов.\n\n"
        "✍️ Это поможет нам лучше понять вашу цель обращения и быстрее вам помочь.\n\n"
        "👋 Good afternoon! Please answer a few questions.\n\n"
        "✍️ This will help us better understand why you are contacting us and assist you more efficiently.",
        reply_markup=reply_markup
    )
    return LANG

# Выбор языка
async def lang_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data
    user_data_temp['language'] = lang

    if lang == 'RU':
        text = "Выберите ваш пол:"
        keyboard = [
            [InlineKeyboardButton("Мужской", callback_data='Мужской'),
             InlineKeyboardButton("Женский", callback_data='Женский')]
        ]
    else:
        text = "Select your gender:"
        keyboard = [
            [InlineKeyboardButton("Male", callback_data='Male'),
             InlineKeyboardButton("Female", callback_data='Female')]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(text, reply_markup=reply_markup)
    return GENDER

# Выбор пола
async def gender_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_data_temp['gender'] = query.data

    lang = user_data_temp['language']
    if lang == 'RU':
        text = "Введите ваш возраст:"
    else:
        text = "Enter your age:"

    await query.message.reply_text(text)
    return AGE

# Ввод возраста
async def age_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_temp['age'] = update.message.text
    lang = user_data_temp['language']

    if lang == 'RU':
        text = "Введите вашу страну проживания:"
    else:
        text = "Enter your country of residence:"

    await update.message.reply_text(text)
    return COUNTRY

# Ввод страны
async def country_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_temp['country'] = update.message.text
    lang = user_data_temp['language']

    if lang == 'RU':
        text = "Были ли вы на международных сайтах знакомств ранее?"
        keyboard = [
            [InlineKeyboardButton("Да", callback_data='Да'),
             InlineKeyboardButton("Нет", callback_data='Нет')]
        ]
    else:
        text = "Have you registered on international dating sites before?"
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data='Yes'),
             InlineKeyboardButton("No", callback_data='No')]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)
    return EXPERIENCE

# Опыт на международных сайтах
async def experience_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_data_temp['experience'] = query.data

    lang = user_data_temp['language']
    if lang == 'RU':
        text = "С какой целью вас интересует регистрация?"
    else:
        text = "What is your purpose for registration?"

    await query.message.reply_text(text)
    return PURPOSE

# Цель регистрации
async def purpose_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_temp['purpose'] = update.message.text
    lang = user_data_temp['language']

    # Отправка админу
    username = update.message.from_user.username or "не указан"
    first_name = update.message.from_user.first_name or ""
    message_admin = (
        f"Username: @{username}\n"
        f"Имя: {first_name}\n"
        f"Язык: {'Русский' if lang == 'RU' else 'English'}\n"
        f"Пол: {user_data_temp['gender']}\n"
        f"Возраст: {user_data_temp['age']}\n"
        f"Страна: {user_data_temp['country']}\n"
        f"Был(а) на международных сайтах: {user_data_temp['experience']}\n"
        f"Цель регистрации: {user_data_temp['purpose']}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=message_admin)

    # Финальное сообщение пользователю
    keyboard = [
        [InlineKeyboardButton("📩 НАПИСАТЬ НАМ", url="https://t.me/YOUR_CHANNEL_OR_BOT")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if lang == 'RU':
        final_text = "Спасибо за ответы! ❤️\n\nНажмите кнопку ниже и отправьте нам сообщение, чтобы мы могли связаться с вами."
    else:
        final_text = "Thank you for your answers! ❤️\n\nPress the button below and send us a message so we can contact you."

    await update.message.reply_text(final_text, reply_markup=reply_markup)

    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Отменено.')
    return ConversationHandler.END

def main():
    BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANG: [CallbackQueryHandler(lang_choice)],
            GENDER: [CallbackQueryHandler(gender_choice)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age_input)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country_input)],
            EXPERIENCE: [CallbackQueryHandler(experience_choice)],
            PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, purpose_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
















