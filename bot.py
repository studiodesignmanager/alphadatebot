import json
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

ADMIN_ID = 486225736

# Загрузка текстов
with open("texts.json", "r", encoding="utf-8") as f:
    texts = json.load(f)

LANG, Q1, Q2 = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    buttons = [["РУССКИЙ", "ENGLISH"]]
    if user_id == ADMIN_ID:
        buttons[0].append("Настройки")  # Добавляем кнопку настройки только админу
    reply_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите язык / Select language:", reply_markup=reply_markup)
    return LANG

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_key = None
    text = update.message.text
    if text == "РУССКИЙ":
        lang_key = "ru"
    elif text == "ENGLISH":
        lang_key = "en"
    elif text == "Настройки" and user_id == ADMIN_ID:
        await update.message.reply_text("Админка: Здесь можно редактировать тексты (реализация отдельно)")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, выберите язык из клавиатуры.")
        return LANG

    context.user_data['lang'] = lang_key
    await update.message.reply_text(texts[lang_key]["question_1"], reply_markup=ReplyKeyboardRemove())
    return Q1

async def question1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_key = context.user_data['lang']
    answer1 = update.message.text
    context.user_data['answer1'] = answer1

    # Отправляем ответ админу сразу с логином или ссылкой
    username = update.effective_user.username
    contact = f"@{username}" if username else f"https://t.me/{update.effective_user.id}"
    admin_message = (f"Ответ 1 от пользователя {contact}:\n{answer1}")
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

    await update.message.reply_text(texts[lang_key]["question_2"])
    return Q2

async def question2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_key = context.user_data['lang']
    answer2 = update.message.text
    context.user_data['answer2'] = answer2

    # Отправляем ответ админу сразу с логином или ссылкой
    username = update.effective_user.username
    contact = f"@{username}" if username else f"https://t.me/{update.effective_user.id}"
    admin_message = (f"Ответ 2 от пользователя {contact}:\n{answer2}")
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

    await update.message.reply_text(texts[lang_key]["final"])
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена. До свидания!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    # Здесь впиши свой токен, который у тебя работал (НЕ ЗАМЕНЯЙ на переменные окружения)
    BOT_TOKEN = "7110528714:AAG0mSUIkaEsbsJBL4FeCIq461HI2-xqx0g"

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question1)],
            Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question2)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()











