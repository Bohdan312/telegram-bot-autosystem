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

# 🔐 1. Завантажуємо змінні середовища
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
creds_b64 = os.getenv("GOOGLE_CREDENTIALS_JSON_BASE64")

if not BOT_TOKEN:
    raise Exception("❌ BOT_TOKEN не встановлено у .env")
if not creds_b64:
    raise Exception("❌ GOOGLE_CREDENTIALS_JSON_BASE64 не знайдено або порожній!")

# 📤 2. Розкодовуємо Base64 і створюємо JSON-файл, якщо ще не створений
try:
    creds_json = base64.b64decode(creds_b64).decode("utf-8")
except Exception as e:
    raise Exception(f"❌ Помилка при декодуванні base64: {e}")

if not creds_json.strip().startswith("{"):
    raise Exception("❌ Розкодовано, але це не JSON! Схоже, змінна має неправильне значення.")

if not os.path.exists("telegram-sheet-writer.json"):
    with open("telegram-sheet-writer.json", "w") as f:
        f.write(creds_json)

# 🔗 3. Підключення до Google Таблиці
try:
    gc = gspread.service_account(filename='telegram-sheet-writer.json')
except Exception as e:
    raise Exception(f"❌ Помилка підключення до Google Sheets: {e}")

sheet_url = "https://docs.google.com/spreadsheets/d/12Y4cvC1mxzq42n2mNHv4RwUuTEfNjMTXLppnUBdITFg/edit#gid=0"
sheet = gc.open_by_url(sheet_url).sheet1

# 🚦 4. Стани
NAME, PHONE = range(2)

# 🟢 5. Команди та обробники
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

    # ✅ Валідація телефону
    if not phone.startswith("+") or not phone[1:].isdigit():
        await update.message.reply_text("❗ Номер має починатись з + і містити лише цифри.")
        return PHONE

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

# 🛠️ 6. Логування
logging.basicConfig(level=logging.INFO)

# 🚀 7. Основна функція запуску
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

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

# ⏯️ 8. Запуск
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
