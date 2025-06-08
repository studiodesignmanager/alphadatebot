import os
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

# Файл с текстами
TEXTS_FILE = "texts.json"

# Состояния для ConversationHandler редактирования текстов
(
    CHOOSING_TEXT,
    TYPING_NEW_TEXT,
) = range(2)

# Состояния для вопросов после /start (задание вопросов пользователю)
ASKING_QUESTIONS = range(10)  # достаточно много для последовательных вопросов

# Загрузка текстов из файла
def load_texts():
    try:
        with open(TEXTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        default_texts = {
            "welcome_message": "Добро пожаловать!",
            "first_question": "У вас были регистрации на международных сайтах знакомств ранее?",
            "second_question": "Сколько вам лет?",
            "third_question": "Каковы ваши интересы?",
        }
        with open(TEXTS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_texts, f, ensure_ascii=False, indent=2)
        return default_texts

# Сохранение текстов
def save_texts(texts):
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

# Загружаем тексты при старте
texts = load_texts()

# Админ ID
ADMIN_ID = 486225736  # <-- Твой Telegram ID

# Список ключей вопросов для упрощения
QUESTION_KEYS = [
    "welcome_message",
    "first_question",
    "second_question",
    "third_question",
]

# /start — задаём вопросы по очереди
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["question_index"] = 0
    await update.message.reply_text(texts["welcome_message"])
    # Задаём первый вопрос
    await update.message.reply_text(texts["first_question"])
    return ASKING_QUESTIONS

# Обработка ответов пользователя на вопросы
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data.get("question_index", 0)
    user_answers = context.user_data.get("answers", {})
    key = QUESTION_KEYS[index]

    user_answers[key] = update.message.text
    context.user_data["answers"] = user_answers

    index += 1
    if index < len(QUESTION_KEYS) - 1:
        context.user_data["question_index"] = index
        # Задаём следующий вопрос
        next_key = QUESTION_KEYS[index]
        await update.message.reply_text(texts[next_key])
        return ASKING_QUESTIONS
    else:
        # Все вопросы заданы, завершаем
        await update.message.reply_text("Спасибо за ответы! Если хотите, можете начать заново командой /start.")
        return ConversationHandler.END

# Команда админа для редактирования текстов
async def edit_texts_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return ConversationHandler.END

    # Клавиатура с названиями всех текстов для редактирования
    reply_keyboard = [[
        "Приветствие",
        "Первый вопрос",
        "Второй вопрос",
        "Третий вопрос",
    ], ["Отмена"]]

    await update.message.reply_text(
        "Что хотите отредактировать?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSING_TEXT

# Выбор текста для редактирования
async def choose_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_choice = update.message.text
    if text_choice == "Отмена":
        await update.message.reply_text("Редактирование отменено.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    context.user_data["edit_choice"] = text_choice

    # Получаем текущий текст по выбору
    mapping = {
        "Приветствие": "welcome_message",
        "Первый вопрос": "first_question",
        "Второй вопрос": "second_question",
        "Третий вопрос": "third_question",
    }

    key = mapping.get(text_choice)
    if not key:
        await update.message.reply_text("Ошибка выбора.")
        return ConversationHandler.END

    current_value = texts.get(key, "")
    await update.message.reply_text(
        f"Текущий текст для '{text_choice}':\n\n{current_value}\n\nОтправьте новый текст:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return TYPING_NEW_TEXT

# Сохранение нового текста
async def save_new_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    choice = context.user_data.get("edit_choice")

    mapping = {
        "Приветствие": "welcome_message",
        "Первый вопрос": "first_question",
        "Второй вопрос": "second_question",
        "Третий вопрос": "third_question",
    }

    key = mapping.get(choice)
    if not key:
        await update.message.reply_text("Произошла ошибка.")
        return ConversationHandler.END

    texts[key] = new_text
    save_texts(texts)
    await update.message.reply_text(f"Текст '{choice}' обновлён успешно!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    print(f"Using BOT_TOKEN: {BOT_TOKEN}")  # Временно для отладки

    if not BOT_TOKEN:
        raise RuntimeError("Error: BOT_TOKEN environment variable is not set!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Хендлер для опроса пользователя (после /start)
    ask_questions_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING_QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    # Хендлер для редактирования текстов админом
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

    app.add_handler(ask_questions_handler)
    app.add_handler(conv_handler_edit_texts)

    app.run_polling()

if __name__ == "__main__":
    main()



