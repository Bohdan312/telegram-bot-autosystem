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


import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

TOKEN = "8026296885:AAHRIsqad7-M-1MjlmaweImA6AhFOJPrp5c"

# Стан форми
NAME, CONTACT, NEED, FOLLOWUP = range(4)

# Прапорець, щоб не запускати форму повторно
submitted_users = set()

# /start
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

async def show_examples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛠 Приклади рішень, які я створював:\n\n"
        "1. Бот-заявка для інстаграм-експерта\n"
        "2. Автовідповідач для онлайн-школи\n"
        "3. Система бронювання через Telegram\n\n"
        "Хочу зробити бот під вашу задачу — просто напишіть, що потрібно."
    )
    await update.message.reply_text(text)

async def trigger_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in submitted_users:
        return ConversationHandler.END
    await update.message.reply_text("💼 Як вас звати?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("📱 Залиште, будь ласка, контакт (Telegram @, телефон):")
    return CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text
    await update.message.reply_text("💬 Що потрібно автоматизувати / для чого бот?")
    return NEED

async def get_need(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["need"] = update.message.text
    name = context.user_data["name"]
    contact = context.user_data["contact"]
    need = context.user_data["need"]
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Зберігаємо в таблицю
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("telegram-sheet-writer.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Telegram_Zayavky").worksheet("Лист1")
        sheet.append_row([name, contact, need, date])
    except Exception as e:
        print(f"Google Sheets помилка: {e}")

    summary = f"📥 Нова заявка:\n👤 Ім’я: {name}\n⏰ Контакт: {contact}\n💬 Потреба: {need}"
    await context.bot.send_message(chat_id=661952434, text=summary)

    # Прапорець
    submitted_users.add(update.message.from_user.id)

    # Варіанти дій далі
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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Дію скасовано.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, trigger_form)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            NEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_need)],
            FOLLOWUP: [MessageHandler(filters.ALL, lambda u, c: ConversationHandler.END)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Приклади ботів"), show_examples))
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_followup)],
        states={FOLLOWUP: [CallbackQueryHandler(handle_followup)]},
        fallbacks=[]
    ))
    app.add_handler(conv_handler)

    print("🚀 Бот запущено з автоворонкою!")
    app.run_polling()
