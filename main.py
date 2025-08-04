import os
import base64
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackContext, CallbackQueryHandler, ConversationHandler, ContextTypes
)

# 🔐 Розкодовуємо облікові дані Google
creds_b64 = os.getenv("GOOGLE_CREDENTIALS_JSON_BASE64")
if not creds_b64:
    raise Exception("❌ GOOGLE_CREDENTIALS_JSON_BASE64 не знайдено!")

try:
    creds_dict = json.loads(base64.b64decode(creds_b64))
except Exception as e:
    raise Exception(f"❌ Помилка при декодуванні або JSON: {e}")

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(creds)

# 🔗 Відкриття Google Таблиці
sheet_url = "https://docs.google.com/spreadsheets/d/12Y4cvC1mxzq42n2mNHv4RwUuTEfNjMTXLppnUBdITFg/edit#gid=0"
sheet = gc.open_by_url(sheet_url).sheet1

# 🚦 ConversationHandler
NAME, PHONE = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚀 Співпраця", callback_data='apply')]]
    await update.message.reply_text("Привіт! Обери дію:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Введи своє ім’я:")
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
        logging.error(f"Помилка запису у Google Sheet: {e}")
        await update.message.reply_text("❌ Виникла помилка при збереженні заявки.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.")
    return ConversationHandler.END

logging.basicConfig(level=logging.INFO)

async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise Exception("❌ BOT_TOKEN не знайдено!")
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

    print("🚀 Бот запущено на Pella!")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
