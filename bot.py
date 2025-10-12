from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
ADMIN_ID = 486225736

LANGUAGE, QUESTION1, QUESTION2, END = range(4)

# Хранение текстов
texts = {
    "greeting": "👋 Добрый день! Пожалуйста, ответьте на несколько вопросов.\n\n"
                "✍️ Это поможет нам лучше понять вашу цель обращения и быстрее вам помочь.\n\n"
                "👋 Good afternoon! Please answer a few questions.\n\n"
                "✍️ This will help us better understand why you are contacting us and assist you more efficiently.",
    "question1": {
        "RU": "Ваш пол?",
        "EN": "Your gender?"
    },
    "question2": {
        "RU": "Ваш полный возраст?",
        "EN": "Your full age?"
    },
    "final": {
        "RU": "Спасибо за ответы!",
        "EN": "Thank you for your responses!"
    }
}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("РУССКИЙ", callback_data="RU"),
         InlineKeyboardButton("ENGLISH", callback_data="EN")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(texts["greeting"], reply_markup=reply_markup)
    return LANGUAGE

# Выбор языка
async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    language = query.data
    context.user_data["lang"] = language
    await query.message.reply_text(texts["question1"][language])
    return QUESTION1

# Вопрос 1
async def question1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer1"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts["question2"][lang])
    return QUESTION2

# Вопрос 2 и завершение
async def question2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer2"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(texts["final"][lang])

    # Отправка админу
    user = update.effective_user
    answers = f"New response from @{user.username if user.username else user.first_name}:\n"
    answers += f"Question 1: {context.user_data['answer1']}\n"
    answers += f"Question 2: {context.user_data['answer2']}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=answers)

    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Conversation canceled.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE: [CallbackQueryHandler(language_choice)],
            QUESTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question1)],
            QUESTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question2)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()


















