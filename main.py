from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from datetime import datetime
import os
import json
import gspread
from google.oauth2.service_account import Credentials

# ⛓️ Авторизація через GOOGLE_CREDENTIALS_JSON (у Render => Environment)
creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
creds = Credentials.from_service_account_info(
    creds_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)
gc = gspread.authorize(creds)
sheet = gc.open("Telegram_Zayavky").worksheet("Лист1")

# 🤖 Telegram Token
TOKEN = os.environ.get("BOT_TOKEN") or "8026296885:AAHRIsqad7-M-1MjlmaweImA6AhFOJPrp5c"

# 🔁 Стан форми
NAME, CONTACT, NEED, FOLLOWUP = range(4)
submitted_users = set()

# 🚪 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Привіт! Якщо вам потрібен ефективний Telegram-бот — ви в правильному місці.\n\n"
        "Я створюю кастомні рішення для бізнесу, автоматизації та продажів.\n\n"
        "✅ Кожен бот — це конкретна користь:\n"
        "• Автозбір заявок\n"
        "• Продаж через воронку\n"
        "• Кастомні функції під нішу\n\n"
        "🔽 Напишіть коротко, що саме вам потрібно — і я запропоную рішення."
    )
    reply_markup = ReplyKeyboardMarkup([["Приклади ботів"]], resize_keyboard=True)
    await update.message.reply_text(text, reply_markup=reply_markup)
    return ConversationHandler.END

# 📌 Приклади
async def show_examples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛠 Приклади рішень, які я створював:\n\n"
        "1. Бот-заявка для інстаграм-експерта\n"
        "2. Автовідповідач для онлайн-школи\n"
        "3. Система бронювання через Telegram\n\n"
        "Хочу зробити бот під вашу задачу — просто напишіть, що потрібно."
    )
    await update.message.reply_text(text)

# ▶️ Початок форми
async def trigger_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in submitted_users:
        await update.message.reply_text("🔁 Ви вже залишали заявку. Натисніть '🔁 Залишити ще заявку' щоб почати нову.")
        return ConversationHandler.END
    await update.message.reply_text("💼 Як вас звати?")
    return NAME

# 🧾 Крок 1
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("📱 Залиште, будь ласка, контакт (Telegram @, телефон):")
    return CONTACT

# 🧾 Крок 2
async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text
    await update.message.reply_text("💬 Що потрібно автоматизувати / для чого бот?")
    return NEED

# 🧾 Крок 3
async def get_need(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["need"] = update.message.text
    name = context.user_data["name"]
    contact = context.user_data["contact"]
    need = context.user_data["need"]
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 💾 Збереження у Google Таблицю
    try:
        sheet.append_row([name, contact, need, date])
    except Exception as e:
        print(f"Google Sheets помилка: {e}")

    # 📩 Повідомлення адміну
    summary = f"📥 Нова заявка:\n👤 Ім’я: {name}\n📱 Контакт: {contact}\n💬 Потреба: {need}"
    await context.bot.send_message(chat_id=661952434, text=summary)

    submitted_users.add(update.message.from_user.id)

    # ➕ Кнопки після заявки
    keyboard = [[
        InlineKeyboardButton("🔁 Залишити ще заявку", callback_data="new_form"),
        InlineKeyboardButton("📆 Консультація", callback_data="book_call")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ Дякую, я отримав заявку і вже працюю над відповіддю! Що далі?",
        reply_markup=reply_markup
    )
    return FOLLOWUP

# 🔄 Обробка після заявки
async def handle_followup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "new_form":
        submitted_users.discard(query.from_user.id)
        await query.message.reply_text("💼 Як вас звати?")
        return NAME

    elif query.data == "book_call":
        await query.message.reply_text(
            "🗓 Щоб забронювати консультацію — напишіть мені 👉 @formbot_xx_bot\n"
            "⚡️ Або надішліть зручний час, я підлаштуюсь."
        )
        return ConversationHandler.END

# ❌ /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Дію скасовано.")
    return ConversationHandler.END

# 🧼 Завершення
async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END

# ▶️ Запуск
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, trigger_form)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            NEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_need)],
            FOLLOWUP: [MessageHandler(filters.ALL, end_conversation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Приклади ботів"), show_examples))
    app.add_handler(CallbackQueryHandler(handle_followup))
    app.add_handler(conv_handler)

    print("🚀 Бот запущено з автоворонкою!")
    app.run_polling()
