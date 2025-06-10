

import json
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
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

ADMIN_ID = 486225736
BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"  # <-- сюда ставь свой токен

LANG, Q1, Q2, FINAL, ADMIN_MENU, EDIT_LANG, EDIT_TEXT = range(7)

# Загрузка текстов из файла
def load_texts():
    try:
        with open("texts.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "ru": {
                "question_1": "У вас были регистрации на международных сайтах знакомствах ранее?",
                "question_2": "С какой целью интересует регистрация?",
                "final": "Спасибо! Мы свяжемся с вами в ближайшее время"
            },
            "en": {
                "question_1": "Have you registered on any international dating sites before?",
                "question_2": "What is your reason for signing up?",
                "final": "Thank you! We will get in touch with you shortly."
            }
        }

# Сохранение текстов в файл
def save_texts(texts):
    with open("texts.json", "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

texts = load_texts()

# Старт — выбор языка, + кнопка Настройки для админа
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    buttons = [["РУССКИЙ", "ENGLISH"]]
    if user_id == ADMIN_ID:
        buttons[0].append("Настройки")
    reply_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите язык / Select language:", reply_markup=reply_markup)
    return LANG

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.lower()
    if choice == "настройки":
        # Переход в меню админа
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
    # Спрашиваем первый вопрос
    await update.message.reply_text(texts[context.user_data["lang"]]["question_1"], reply_markup=ReplyKeyboardRemove())
    return Q1

async def q1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q1"] = update.message.text
    await update.message.reply_text(texts[context.user_data["lang"]]["question_2"])
    return Q2

async def q2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q2"] = update.message.text
    await update.message.reply_text(texts[context.user_data["lang"]]["final"])
    # Отправляем ответы админу сразу
    admin_msg = f"Ответы пользователя @{update.effective_user.username or '[нет username]'} (id: {update.effective_user.id}):\n" \
                f"Язык: {context.user_data['lang']}\n" \
                f"Вопрос 1: {context.user_data['q1']}\n" \
                f"Вопрос 2: {context.user_data['q2']}\n" \
                f"https://t.me/{update.effective_user.username}" if update.effective_user.username else f"tg://user?id={update.effective_user.id}"
    try:
        await context.bot.send_message(ADMIN_ID, admin_msg)
    except Exception:
        pass
    return ConversationHandler.END

# Админка: выбор языка для редактирования или возврат назад
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.lower()
    if choice == "назад":
        # Возврат к выбору языка для пользователя
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
    # Выбор текста для редактирования
    await update.message.reply_text(
        f"Выберите текст для редактирования ({context.user_data['edit_lang']}):",
        reply_markup=ReplyKeyboardMarkup([["question_1", "question_2", "final"], ["Назад"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return EDIT_LANG

async def edit_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.lower()
    if choice == "назад":
        # Возврат в меню админа — выбор языка
        await update.message.reply_text(
            "Админка: Выберите язык для редактирования:",
            reply_markup=ReplyKeyboardMarkup([["RU", "EN"], ["Назад"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return ADMIN_MENU
    if choice not in ["question_1", "question_2", "final"]:
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
    # После сохранения — возвращаем в меню редактирования языков
    await update.message.reply_text(
        "Админка: Выберите язык для редактирования:",
        reply_markup=ReplyKeyboardMarkup([["RU", "EN"], ["Назад"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return ADMIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
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
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()










