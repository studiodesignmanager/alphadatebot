import logging
import json
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

BOT_TOKEN = "7110528714:AAG0mSUIkaEsbsJBL4FeCIq461HI2-xqx0g"
ADMIN_ID = 486225736

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

LANGUAGE, QUESTION1, QUESTION2 = range(3)

TEXTS_FILE = Path(__file__).parent / "texts.json"
if not TEXTS_FILE.exists():
    raise FileNotFoundError("Файл texts.json не найден!")

with open(TEXTS_FILE, "r", encoding="utf-8") as f:
    texts = json.load(f)

def save_texts():
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["РУССКИЙ", "ENGLISH"]]
    await update.message.reply_text(
        "Выберите язык / Choose your language:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return LANGUAGE

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "РУССКИЙ":
        context.user_data["lang"] = "ru"
    elif text == "ENGLISH":
        context.user_data["lang"] = "en"
    else:
        await update.message.reply_text("Пожалуйста, выберите язык с помощью кнопок.")
        return LANGUAGE

    await update.message.reply_text(
        texts[context.user_data["lang"]]["question_1"],
        reply_markup=ReplyKeyboardRemove(),
    )
    return QUESTION1

async def question1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    context.user_data["answer_1"] = answer

    # Отправляем админу сообщение с ответом
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Ответ на первый вопрос от пользователя {update.effective_user.id} ({update.effective_user.full_name}):\n{answer}"
    )

    await update.message.reply_text(texts[context.user_data["lang"]]["question_2"])
    return QUESTION2

async def question2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    context.user_data["answer_2"] = answer

    # Отправляем админу сообщение с ответом
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Ответ на второй вопрос от пользователя {update.effective_user.id} ({update.effective_user.full_name}):\n{answer}"
    )

    await update.message.reply_text(texts[context.user_data["lang"]]["final"])
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Админка для редактирования текстов

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Доступ запрещён.")
        return

    msg = "Текущие тексты:\n\n"
    for lang_code, vals in texts.items():
        msg += f"[{lang_code}]\n"
        for key, val in vals.items():
            msg += f"{key}: {val}\n"
        msg += "\n"
    msg += (
        "Чтобы изменить текст, отправьте сообщение в формате:\n"
        "lang|key|новый текст\n"
        "Например:\n"
        "ru|question_1|Новый текст вопроса"
    )
    await update.message.reply_text(msg)

async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return  # Игнорируем сообщения не от админа

    text = update.message.text
    if "|" not in text:
        return  # Это не команда редактирования, игнорируем

    try:
        lang, key, new_text = text.split("|", 2)
        lang = lang.strip().lower()
        key = key.strip()
        new_text = new_text.strip()

        if lang in texts and key in texts[lang]:
            texts[lang][key] = new_text
            save_texts()
            await update.message.reply_text("Текст успешно обновлён.")
        else:
            await update.message.reply_text("Ошибка: неверный язык или ключ.")
    except Exception as e:
        await update.message.reply_text("Ошибка формата. Используйте: lang|key|новый текст")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            QUESTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question1)],
            QUESTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question2)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("edit", edit))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit))

    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()







