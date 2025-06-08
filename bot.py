import json
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Логи
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Пути к файлу с текстами
TEXTS_FILE = "texts.json"

# Константы состояний ConversationHandler для редактирования
(
    CHOOSING_TEXT,
    TYPING_NEW_TEXT,
) = range(2)

# Загрузка текстов из файла
def load_texts():
    try:
        with open(TEXTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Если файл отсутствует, создадим с дефолтными текстами
        default_texts = {
            "welcome_message": "Добро пожаловать!",
            "first_question": "У вас были регистрации на международных сайтах знакомств ранее?"
        }
        with open(TEXTS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_texts, f, ensure_ascii=False, indent=2)
        return default_texts

# Сохранение текстов в файл
def save_texts(texts):
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

# Загружаем тексты при старте
texts = load_texts()

# Админ ID (замени на свой)
ADMIN_ID = 123456789  # <- Твой Telegram ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(texts["welcome_message"])
    # Сразу после приветствия задаём первый вопрос
    await update.message.reply_text(texts["first_question"])

# Команда админа для редактирования текстов
async def edit_texts_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return ConversationHandler.END

    reply_keyboard = [["Приветствие", "Первый вопрос"], ["Отмена"]]
    await update.message.reply_text(
        "Что хотите отредактировать?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSING_TEXT

async def choose_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_choice = update.message.text
    if text_choice == "Отмена":
        await update.message.reply_text("Редактирование отменено.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    context.user_data["edit_choice"] = text_choice
    current_value = (
        texts["welcome_message"] if text_choice == "Приветствие" else texts["first_question"]
    )
    await update.message.reply_text(
        f"Текущий текст для '{text_choice}':\n\n{current_value}\n\nОтправьте новый текст:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return TYPING_NEW_TEXT

async def save_new_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    choice = context.user_data.get("edit_choice")

    if choice == "Приветствие":
        texts["welcome_message"] = new_text
    elif choice == "Первый вопрос":
        texts["first_question"] = new_text
    else:
        await update.message.reply_text("Произошла ошибка.")
        return ConversationHandler.END

    save_texts(texts)
    await update.message.reply_text(f"Текст '{choice}' обновлён успешно!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()

    # Хендлеры
    conv_handler_edit_texts = ConversationHandler(
        entry_points=[CommandHandler("edit_texts", edit_texts_start)],
        states={
            CHOOSING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_text)],
            TYPING_NEW_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler_edit_texts)

    # Запуск бота
    app.run_polling()

if __name__ == "__main__":
    main()


