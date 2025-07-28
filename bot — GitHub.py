import requests
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from config import TELEGRAM_TOKEN  # 🔐 Token is now taken from config.py

user_states = {}

def get_currency_rates():
    try:
        response = requests.get("https://open.er-api.com/v6/latest/UAH")
        data = response.json()
        if data.get("result") != "success":
            return "⚠️ Failed to get currency rates."

        rates = data["rates"]
        today = datetime.now().strftime('%d.%m.%Y')

        return (
            f"💱 Currency rates as of {today} (for 1 UAH):\n"
            f"USD: {round(rates.get('USD', 0), 4)}\n"
            f"EUR: {round(rates.get('EUR', 0), 4)}\n"
            f"PLN: {round(rates.get('PLN', 0), 4)}\n"
            f"GBP: {round(rates.get('GBP', 0), 4)}\n"
            f"BTC: {round(rates.get('BTC', 0), 6)}"
        )
    except Exception as e:
        return f"⚠️ Error while fetching data: {e}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💱 Currency Rates", callback_data='rate')],
        [InlineKeyboardButton("🔁 Send rates now", callback_data='now')],
        [InlineKeyboardButton("💱 Convert Amount", callback_data='convert')],
        [
            InlineKeyboardButton("✅ Subscribe", callback_data='subscribe'),
            InlineKeyboardButton("❌ Unsubscribe", callback_data='unsubscribe'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an action:", reply_markup=reply_markup)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data in ['rate', 'now']:
        text = get_currency_rates()
        await query.edit_message_text(text=text)

    elif query.data == 'convert':
        user_states[user_id] = 'awaiting_amount'
        await query.edit_message_text("💬 Enter the amount in UAH you want to convert:")

    elif query.data == 'subscribe':
        await query.edit_message_text("🔔 You have subscribed to currency rate updates (this feature is under development).")

    elif query.data == 'unsubscribe':
        await query.edit_message_text("🔕 You have unsubscribed from currency rate updates.")


async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_states.get(user_id) != 'awaiting_amount':
        return

    try:
        amount = float(text.replace(" ", "").replace(",", "."))

        response = requests.get("https://open.er-api.com/v6/latest/UAH")
        data = response.json()
        if data.get("result") != "success":
            await update.message.reply_text("⚠️ Failed to get currency rates.")
            return

        rates = data["rates"]
        usd = round(rates.get("USD", 0) * amount, 2)
        eur = round(rates.get("EUR", 0) * amount, 2)
        pln = round(rates.get("PLN", 0) * amount, 2)
        gbp = round(rates.get("GBP", 0) * amount, 2)
        btc = round(rates.get("BTC", 0) * amount, 6)

        reply = (
            f"💱 Conversion of {amount} UAH:\n"
            f"USD: {usd}\n"
            f"EUR: {eur}\n"
            f"PLN: {pln}\n"
            f"GBP: {gbp}\n"
            f"BTC: {btc}"
        )

        await update.message.reply_text(reply)

    except ValueError:
        await update.message.reply_text("❌ Please enter the amount as a number, e.g., `1000`", parse_mode='Markdown')
    finally:
        user_states[user_id] = None


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))

    print("✅ Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
