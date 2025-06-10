import logging
import json
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 486225736  # замените на свой admin ID
BOT_TOKEN = "7110528714:AAG0mSUIkaEsbsJBL4FeCIq461HI2-xqx0g"  # Токен бота здесь, строкой

# Состояния разговора
LANGUAGE, Q1, Q2, FINAL = range(4)

with open("texts.json", "r", encoding="utf-8") as f:
    texts = json.load(f)

def is_admin(user_id):
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.id)
    # Клавиатура выбора языка
    keyboard = [
        [KeyboardButton("РУССКИЙ"), KeyboardButton("ENGLISH")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Please select your language / Пожалуйста, выберите язык:",
        reply_markup=reply_markup,
    )
    return LANGUAGE

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    lang_text = update.message.text.lower()
    if lang_text.startswith("ру"):
        context.user_data["lang"] = "ru"
    elif lang_text.startswith("en"):
        context.user_data["lang"] = "en"
    else:
        await update.message.reply_text("Please select a valid language.")
        return LANGUAGE

    lang = context.user_data["lang"]
    # Отправляем первый вопрос
    await update.message.reply_text(texts[lang]["question_1"], reply_markup=ReplyKeyboardRemove())
    return Q1

async def q1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    answer = update.message.text
    context.user_data["answer_1"] = answer

    # Отправляем ответ админу сразу
    await send_answer_to_admin(user, 1, answer, context)

    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["question_2"])
    return Q2

async def q2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    answer = update.message.text
    context.user_data["answer_2"] = answer

    # Отправляем ответ админу сразу
    await send_answer_to_admin(user, 2, answer, context)

    lang = context.user_data["lang"]
    await update.message.reply_text(texts[lang]["final"])

    # Отправляем финальное сообщение админу
    await send_final_message_to_admin(user, context)

    return ConversationHandler.END

async def send_answer_to_admin(user, q_num, answer, context):
    username = user.username
    user_id = user.id
    if username:
        user_info = f"@{username}"
    else:
        user_info = f"https://t.me/user?id={user_id}"
    msg = f"Ответ пользователя {user_info} на вопрос {q_num}:\n{answer}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

async def send_final_message_to_admin(user, context):
    username = user.username
    user_id = user.id
    if username:
        user_info = f"@{username}"
    else:
        user_info = f"https://t.me/user?id={user_id}"
    msg = f"Пользователь {user_info} завершил опрос."
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

# Команда /settings только для админа
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Access denied.")
        return
    # Здесь админ может редактировать тексты, пример:
    await update.message.reply_text("Здесь будет админка для редактирования текстов (пока заглушка).")

# Добавим клавиатуру с кнопкой Настройки для админа
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    buttons = []
    if is_admin(user_id):
        buttons.append([KeyboardButton("Настройки")])
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True) if buttons else None
    await update.message.reply_text("Привет! Выберите действие:", reply_markup=reply_markup)

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    # Обработка нажатия кнопки Настройки
    if text == "Настройки" and is_admin(user_id):
        await settings(update, context)
        return
    # Можно сюда добавить другие обработки кнопок
    await update.message.reply_text("Команда не распознана. Используйте /start.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, q1)],
            Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, q2)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    application.run_polling()

if __name__ == "__main__":
    main()











