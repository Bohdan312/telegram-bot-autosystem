import os
import json
import base64
import logging
import gspread

from google.oauth2.service_account import Credentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackContext, CallbackQueryHandler,
    ConversationHandler, ContextTypes
)

from dotenv import load_dotenv
load_dotenv()

# --- Розкодування Google Credentials з base64 ---
creds_b64 = os.getenv("GOOGLE_CREDENTIALS_JSON_BASE64")
if not creds_b64:
    raise Exception("❌ GOOGLE_CREDENTIALS_JSON_BASE64 не знайдено!")

try:
    creds_json_str = base64.b64decode(creds_b64).decode("utf-8")
    creds_dict = json.loads(creds_json_str)
except Exception as e:
    raise Exception(f"❌ Неможливо декодувати GOOGLE_CREDENTIALS_JSON_BASE64: {e}")

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(creds)

# --- Підключення до Google Sheets ---
sheet_url = "https://docs.google.com/spreadsheets/d/12Y4cvC1mxzq42n2mNHv4RwUuTEfNjMTXLppnUBdITFg/edit#gid=0"
sheet = gc.open_by_url(sheet_url).sheet1

# --- Стани для ConversationHandler ---
NAME, PHONE = range(2)

# --- Команди та обробники ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚀 Співпраця", callback_data='apply')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привіт! Обери дію:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'apply':
        await query.message.reply_text("Введи своє ім’я:")
        return NAME

async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("Тепер введи свій номер телефону:")
    return PHONE

async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data.get('name')
    phone = update.message.text.strip()

    try:
        sheet.append_row([name, phone])
        await update.message.reply_text("✅ Заявку прийнято! Ми зв’яжемося з тобою.")
    except Exception as e:
        logging.error(f"❌ Помилка запису у Google Sheet: {e}")
        await update.message.reply_text("❌ Сталася помилка при збереженні заявки.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.")
    return ConversationHandler.END

# --- Логування ---
logging.basicConfig(level=logging.INFO)

# --- Запуск бота ---
async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise Exception("❌ BOT_TOKEN не встановлено!")

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("🚀 Бот запущено з автоворонкою!")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
