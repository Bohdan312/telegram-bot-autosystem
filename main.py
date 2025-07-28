import os
import base64
import logging
import gspread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackContext, CallbackQueryHandler, ConversationHandler, ContextTypes
)
from dotenv import load_dotenv
load_dotenv()

# 🔐 1. Розкодовуємо облікові дані Google Sheets з base64
creds_b64 = os.getenv("	
ZGYyMzQwNzY3MjUxZGQ5YmVkOWE4NzgzNzMxY2UwYWQ1ZDQ1MTkxYQo=")
if not creds_b64:
    raise Exception("ZGYyMzQwNzY3MjUxZGQ5YmVkOWE4NzgzNzMxY2UwYWQ1ZDQ1MTkxYQo===
")

creds_json = base64.b64decode(creds_b64).decode("utf-8")
with open("telegram-sheet-writer.json", "w") as f:
    f.write(creds_json)

# 🔗 2. Підключення до Google Таблиці (✅ виправлено URL)
gc = gspread.service_account(filename='telegram-sheet-writer.json')
sheet_url = "https://docs.google.com/spreadsheets/d/12Y4cvC1mxzq42n2mNHv4RwUuTEfNjMTXLppnUBdITFg/edit#gid=0"
sheet = gc.open_by_url(sheet_url).sheet1

# 🚦 3. Стани для ConversationHandler
NAME, PHONE = range(2)

# 🔘 4. Стартова команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚀 Співпраця", callback_data='apply')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привіт! Обери дію:", reply_markup=reply_markup)

# 🧷 5. Обробка кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'apply':
        await query.message.reply_text("Введи своє ім’я:")
        return NAME

# 👤 6. Отримуємо ім’я
async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("Тепер введи свій номер телефону:")
    return PHONE

# ☎️ 7. Отримуємо телефон і записуємо в таблицю
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

# ❌ 8. Обробка скасування
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.")
    return ConversationHandler.END

# 🔧 9. Логування
logging.basicConfig(level=logging.INFO)

# 🚀 10. Основна функція запуску
async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise Exception("BOT_TOKEN не встановлено")

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

# ⏯️ Запуск
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
