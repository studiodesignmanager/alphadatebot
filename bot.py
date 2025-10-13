import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import json

# === НАСТРОЙКИ ===
TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"
ADMIN_ID = 486225736

# === ЛОГИ ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# === ЗАГРУЗКА ТЕКСТОВ ===
with open("texts.json", "r", encoding="utf-8") as f:
    texts = json.load(f)

user_data = {}

# === СТАРТ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("РУССКИЙ"), KeyboardButton("ENGLISH")],
    ]
    await update.message.reply_text(
        "Добрый день!\n\nОтветьте, пожалуйста, на несколько вопросов. "
        "Это поможет нам лучше понять цель вашего обращения и помочь вам быстрее.\n\n"
        "Выберите удобный язык:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )

# === ВЫБОР ЯЗЫКА ===
async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text.strip().upper()
    if lang not in ["РУССКИЙ", "ENGLISH"]:
        return

    user_data[update.effective_user.id] = {"lang": lang, "answers": []}
    first_q = texts[lang]["q1"]
    await update.message.reply_text(first_q)

# === ОБРАБОТКА ОТВЕТОВ ===
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        await update.message.reply_text("Введите /start чтобы начать заново.")
        return

    lang = user_data[user_id]["lang"]
    answers = user_data[user_id]["answers"]

    answers.append(update.message.text)

    # Вопросы по порядку
    questions = [texts[lang]["q1"], texts[lang]["q2"], texts[lang]["q3"], texts[lang]["q4"], texts[lang]["q5"]]

    if len(answers) < len(questions):
        await update.message.reply_text(questions[len(answers)])
    else:
        # Отправляем админу
        msg = f"📝 Новая анкета ({lang}):\n\n"
        for i, q in enumerate(questions):
            msg += f"{q}\n➡️ {answers[i]}\n\n"

        if update.effective_user.username:
            msg += f"👤 Username: @{update.effective_user.username}"

        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

        # Финальное сообщение пользователю
        if lang == "РУССКИЙ":
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("📩📩 СВЯЗАТЬСЯ С НАМИ", url="https://t.me/alphadate")]]
            )
            await update.message.reply_text(
                "Спасибо за ваши ответы! ❤️\n\n"
                "Нажмите кнопку ниже, чтобы сразу написать нам и мы свяжемся с вами.",
                reply_markup=keyboard,
            )
        else:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("📩📩 CONTACT US", url="https://t.me/alphadate")]]
            )
            await update.message.reply_text(
                "Thank you for your answers! ❤️\n\n"
                "Click the button below and send us a message so we can get in touch with you.",
                reply_markup=keyboard,
            )

        # очищаем чтобы можно было заполнить заново
        del user_data[user_id]


# === ЗАПУСК ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^(РУССКИЙ|ENGLISH)$"), language_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    app.run_polling()

if __name__ == "__main__":
    main()





















