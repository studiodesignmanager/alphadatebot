import json
import logging
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 486225736
BOT_TOKEN = "7110528714:AAFP6YGssZkEw55Jda1CYY1aR802XGoBOhg"

# Состояния
LANG, GENDER, AGE, COUNTRY, Q1, Q2, FINAL, ADMIN_MENU, EDIT_LANG, EDIT_TEXT = range(10)

# Загрузка текстов
def load_texts():
    try:
        with open("texts.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "ru": {
                "greeting": "Добрый день! Ответьте на несколько вопросов.",
                "gender": "Пожалуйста, выберите ваш пол:",
                "age": "Пожалуйста, укажите ваш возраст",
                "country": "Пожалуйста, укажите страну проживания",
                "question_1": "У вас были регистрации на международных сайтах знакомств ранее?",
                "question_2": "С какой целью интересует регистрация?",
                "final": "Спасибо! Мы свяжемся с вами в ближайшее время",
                "contact_prompt": "Если есть вопросы, нажмите кнопку ниже:",
            },
            "en": {
                "greeting": "Good afternoon! Please answer a few questions.",
                "gender": "Please choose your gender:",
                "age": "Please enter your age",
                "country": "Please enter your country of residence",
                "question_1": "Have you registered on international dating sites before?",
                "question_2": "What is the purpose of your registration?",
                "final": "Thank you! We will contact you shortly",
                "contact_prompt": "If you have additional questions, click the button below:",
            },
        }

def save_texts(texts):
    with open("texts.json", "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

texts = load_texts()

# --- Хендлеры ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [["РУССКИЙ", "ENGLISH"]]
    if update.effective_user.id == ADMIN_ID:
        buttons[0].append("Настройки")
    await update.message.reply_text(
        f"{texts['ru']['greeting']}\n{texts['en']['greeting']}",
        reply_markup=ReplyKeyboardMark_











