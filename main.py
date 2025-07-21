import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

async def get_need(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["need"] = update.message.text
    name = context.user_data["name"]
    contact = context.user_data["contact"]
    need = context.user_data["need"]
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Telegram_Zayavky").worksheet("Лист1")
        sheet.append_row([name, contact, need, date])
    except Exception as e:
        print(f"Google Sheets помилка: {e}")

    summary = f"📥 Нова заявка:\n👤 Ім’я: {name}\n⏰ Контакт: {contact}\n💬 Потреба: {need}"
    await context.bot.send_message(chat_id=661952434, text=summary)

    submitted_users.add(update.message.from_user.id)

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
