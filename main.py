import os
import base64
import logging
import gspread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackContext, CallbackQueryHandler, ConversationHandler
)

# 🔐 Розкодовуємо Google Sheets credentials з base64
creds_b64 = os.getenv("GOOGLE_CREDENTIALS_JSON_BASE64")
if not creds_b64:
    raise Exception("GOOGLE_CREDENTIALS_JSON_BASE64 не знайдено!")

creds_json = base64.b64decode(creds_b64).decode("utf-8")
with open("telegram-sheet-writer.json", "w") as f:
    f.write(creds_json)

# 🔗 Підключення до Google Таблиці
gc = gspread.service_account(filename='telegram-sheet-writer.json')
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/ТУТ_ТВІЙ_ID/edit#gid=0").sheet1  # ← змінити URL

# 🚦 Стани для ConversationHandler
NAME, PHONE = range(2)

# 🔘 Старт
async def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("🚀 Співпраця", callback_data='apply')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привіт! Обери дію:", reply_markup=reply_markup)

# 🧷 Обробка кнопки
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == 'apply':
        await query.message.reply_text("Введи своє ім’я:")
        return NAME

# 👤 Отримуємо ім’я
async def name_handler(update: Update, context: CallbackContext):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Тепер введи свій номер телефону:")
    return PHONE

# ☎️ Отримуємо телефон
async def phone_handler(update: Update, context: CallbackContext):
    name = context.user_data.get('name')
    phone = update.message.text

    # 📝 Запис у Google Таблицю
    sheet.append_row([name, phone])

    await update.message.reply_text("✅ Заявку прийнято! Ми зв’яжемося з тобою.")
    return ConversationHandler.END

# ❌ Вихід
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Скасовано.")
    return ConversationHandler.END

# 🔧 Логування
logging.basicConfig(level=logging.INFO)

# 🚀 Запуск бота
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

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
