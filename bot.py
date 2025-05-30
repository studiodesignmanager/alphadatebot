import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN or not ADMIN_ID:
    raise ValueError("⛔ Убедитесь, что в .env заданы TELEGRAM_TOKEN и ADMIN_ID")

ADMIN_ID = int(ADMIN_ID)

logging.basicConfig(level=logging.INFO)

user_states = {}
user_lang = {}
admin_editing = {}

LANG = {
    "ru": {
        "age_country": "Добрый день! Напишите пожалуйста свой возраст и страну проживания",
        "was_registered": "У вас были регистрации на международных сайтах знакомствах ранее?",
        "purpose": "С какой целью интересует регистрация?",
        "thanks": "Спасибо Мы свяжемся с вами в ближайшее время",
        "choose_lang": "Выберите ваш язык:",
        "menu": "⚙️ Настройки",
        "support": "📞 Поддержка: @alphadate",
    },
    "en": {
        "age_country": "Good day,\nKindly provide your age and the country of your residence",
        "was_registered": "Have you previously registered on any international dating platforms?",
        "purpose": "What is your primary purpose for seeking registration?",
        "thanks": "Thank you We will contact you shortly",
        "choose_lang": "Please choose your language:",
        "menu": "⚙️ Settings",
        "support": "📞 Support: @alphadate",
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_ID

    keyboard = [
        [InlineKeyboardButton("🔴  РУССКИЙ ЯЗЫК", callback_data="lang_ru")],
        [InlineKeyboardButton("🔴  ENGLISH LANGUAGE", callback_data="lang_en")]
    ]

    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ Настройки", callback_data="open_settings")])

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=LANG["ru"]["choose_lang"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = "ru" if query.data == "lang_ru" else "en"
    user_lang[user_id] = lang
    user_states[user_id] = 1
    await query.message.reply_text(LANG[lang]["age_country"])

async def message_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    username = update.effective_user.username or "Без username"

    if user_id in admin_editing:
        lang, field = admin_editing.pop(user_id)
        LANG[lang][field] = text
        await update.message.reply_text(f"✅ Текст для поля `{field}` ({lang}) обновлён.")
        return

    lang = user_lang.get(user_id, "ru")
    step = user_states.get(user_id, 0)

    if ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📩 @{username} ({user_id}) — Шаг {step}:\n{text}"
            )
        except Exception as e:
            print("Ошибка отправки админу:", e)

    if step == 1:
        await update.message.reply_text(LANG[lang]["was_registered"])
        user_states[user_id] = 2
    elif step == 2:
        await update.message.reply_text(LANG[lang]["purpose"])
        user_states[user_id] = 3
    elif step == 3:
        await update.message.reply_text(LANG[lang]["thanks"])
        user_states[user_id] = 0
    else:
        await update.message.reply_text("Пожалуйста, начните с команды /start")

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id != ADMIN_ID:
        await query.message.reply_text("⛔ Только админ может открывать настройки.")
        return

    buttons_ru = {
        "age_country": [InlineKeyboardButton("✏️ Изменить приветствие (RU)", callback_data="edit_ru_age_country")],
        "was_registered": [InlineKeyboardButton("✏️ Изменить вопрос о регистрации (RU)", callback_data="edit_ru_was_registered")],
        "purpose": [InlineKeyboardButton("✏️ Изменить цель регистрации (RU)", callback_data="edit_ru_purpose")],
        "thanks": [InlineKeyboardButton("✏️ Изменить финальное сообщение (RU)", callback_data="edit_ru_thanks")]
    }
    buttons_en = {
        "age_country": [InlineKeyboardButton("✏️ Edit greeting (EN)", callback_data="edit_en_age_country")],
        "was_registered": [InlineKeyboardButton("✏️ Edit registration question (EN)", callback_data="edit_en_was_registered")],
        "purpose": [InlineKeyboardButton("✏️ Edit purpose question (EN)", callback_data="edit_en_purpose")],
        "thanks": [InlineKeyboardButton("✏️ Edit final message (EN)", callback_data="edit_en_thanks")]
    }

    keyboard = []
    for field in ["age_country", "was_registered", "purpose", "thanks"]:
        keyboard.append(buttons_ru[field])
        keyboard.append(buttons_en[field])

    await query.message.reply_text("Выберите, что изменить:", reply_markup=InlineKeyboardMarkup(keyboard))

async def edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if user_id != ADMIN_ID:
        return
    _, lang, field = query.data.split("_", 2)
    admin_editing[user_id] = (lang, field)
    await query.message.reply_text(f"Введите новый текст для `{field}` ({lang}):")

async def support_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = user_lang.get(query.from_user.id, "ru")
    await query.message.reply_text(LANG[lang]["support"])

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_language, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(handle_settings, pattern="^open_settings$"))
    app.add_handler(CallbackQueryHandler(edit_field, pattern="^edit_"))
    app.add_handler(CallbackQueryHandler(support_callback, pattern="^support$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_flow))
    print("✅ Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
