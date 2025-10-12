from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler

# --- Константы для состояний ---
LANG, GENDER, AGE, COUNTRY, INTERNATIONAL, PURPOSE = range(6)

# --- Админ ---
ADMIN_ID = 486225736

# --- Приветствие ---
WELCOME_TEXT = """👋 Добрый день! Пожалуйста, ответьте на несколько вопросов.
✍️ Это поможет нам лучше понять вашу цель обращения и быстрее вам помочь.

👋 Good afternoon! Please answer a few questions.
✍️ This will help us better understand why you are contacting us and assist you more efficiently."""

# --- Кнопки выбора языка ---
language_keyboard = [
    [InlineKeyboardButton("РУССКИЙ", callback_data='ru')],
    [InlineKeyboardButton("ENGLISH", callback_data='en')]
]
language_markup = InlineKeyboardMarkup(language_keyboard)

# --- Хранение данных пользователя ---
user_data_dict = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, reply_markup=language_markup)

# --- Обработка выбора языка ---
async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    user_data_dict[query.from_user.id] = {"lang": lang}
    if lang == 'ru':
        keyboard = [
            [InlineKeyboardButton("Мужской", callback_data='Мужской')],
            [InlineKeyboardButton("Женский", callback_data='Женский')]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("1️⃣ Ваш пол:", reply_markup=markup)
    else:
        keyboard = [
            [InlineKeyboardButton("Male", callback_data='Male')],
            [InlineKeyboardButton("Female", callback_data='Female')]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("1️⃣ Your gender:", reply_markup=markup)
    return GENDER

# --- Пол ---
async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data_dict[query.from_user.id]['gender'] = query.data

    lang = user_data_dict[query.from_user.id]['lang']
    if lang == 'ru':
        await query.message.reply_text("2️⃣ Ваш полный возраст (только цифры):")
    else:
        await query.message.reply_text("2️⃣ Your full age (numbers only):")
    return AGE

# --- Возраст ---
async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.message.from_user.id]['age'] = update.message.text
    lang = user_data_dict[update.message.from_user.id]['lang']
    if lang == 'ru':
        await update.message.reply_text("3️⃣ Ваша страна постоянного проживания?")
    else:
        await update.message.reply_text("3️⃣ Your country of residence?")
    return COUNTRY

# --- Страна ---
async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.message.from_user.id]['country'] = update.message.text
    lang = user_data_dict[update.message.from_user.id]['lang']
    if lang == 'ru':
        keyboard = [
            [InlineKeyboardButton("Да", callback_data='Да')],
            [InlineKeyboardButton("Нет", callback_data='Нет')]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("4️⃣ Были ли у вас регистрации на международных сайтах знакомств ранее?", reply_markup=markup)
    else:
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data='Yes')],
            [InlineKeyboardButton("No", callback_data='No')]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("4️⃣ Have you previously registered on international dating sites?", reply_markup=markup)
    return INTERNATIONAL

# --- Международные сайты ---
async def international(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data_dict[query.from_user.id]['international'] = query.data
    lang = user_data_dict[query.from_user.id]['lang']
    if lang == 'ru':
        await query.message.reply_text("5️⃣ С какой целью вас интересует регистрация?")
    else:
        await query.message.reply_text("5️⃣ What is your purpose for registering?")
    return PURPOSE

# --- Цель регистрации ---
async def purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.message.from_user.id]['purpose'] = update.message.text
    data = user_data_dict[update.message.from_user.id]
    lang = data['lang']

    # --- Отправка администратору ---
    text = f"Username: @{update.message.from_user.username or '-'}\n" \
           f"Имя: {update.message.from_user.full_name}\n" \
           f"Язык: {'Русский' if lang == 'ru' else 'English'}\n" \
           f"Пол: {data['gender']}\n" \
           f"Возраст: {data['age']}\n" \
           f"Страна: {data['country']}\n" \
           f"Был(а) на международных сайтах: {data['international']}\n" \
           f"Цель регистрации: {data['purpose']}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=text)

    # --- Финальное сообщение пользователю ---
    final_text = ("Спасибо за ответы! ❤️\n\n"
                  "Нажмите кнопку ниже и отправьте нам сообщение, чтобы мы могли связаться с вами.")
    keyboard = [[InlineKeyboardButton("📩 НАПИСАТЬ НАМ", url="https://t.me/ВАШ_ТЕЛЕГРАМ_КАНАЛ_ИЛИ_БОТ")]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(final_text, reply_markup=markup)

    return ConversationHandler.END

# --- Отмена ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Процесс прерван.")
    return ConversationHandler.END

# --- Основная функция ---
def main():
    app = ApplicationBuilder().token("ВАШ_BOT_TOKEN").build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANG: [CallbackQueryHandler(choose_language)],
            GENDER: [CallbackQueryHandler(gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country)],
            INTERNATIONAL: [CallbackQueryHandler(international)],
            PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, purpose)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__':
    main()



















