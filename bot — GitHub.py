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

# Словарь для отслеживания состояния пользователей
user_states = {} 

# Получение курса валют
def get_currency_rates():
    try:
        response = requests.get("https://open.er-api.com/v6/latest/UAH")
        data = response.json()
        if data.get("result") != "success":
            return "⚠️ Не удалось получить курс валют: сервер вернул ошибку" #Хуй мне в рот

        rates = data["rates"]
        today = datetime.now().strftime('%d.%m.%Y')

        return (
            f"💱 Курсы валют на {today} (за 1 гривну):\n"
            f"USD: {round(rates.get('USD', 0), 4)}\n"
            f"EUR: {round(rates.get('EUR', 0), 4)}\n"
            f"PLN: {round(rates.get('PLN', 0), 4)}\n"
            f"GBP: {round(rates.get('GBP', 0), 4)}\n"
            f"BTC: {round(rates.get('BTC', 0), 6)}"
        )
    except Exception as e:
        return f"⚠️ Не удалось получить курс валют: {e}"


# Стартовая команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💱 Курс валют", callback_data='rate')],
        [InlineKeyboardButton("🔁 Отправить курс сейчас", callback_data='now')],
        [InlineKeyboardButton("💱 Перевести сумму", callback_data='convert')],
        [
            InlineKeyboardButton("✅ Подписаться", callback_data='subscribe'),
            InlineKeyboardButton("❌ Отписаться", callback_data='unsubscribe'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери действие:", reply_markup=reply_markup)


# Обработка кнопок
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'rate' or query.data == 'now':
        text = get_currency_rates()
        await query.edit_message_text(text=text)

    elif query.data == 'convert':
        user_states[user_id] = 'awaiting_amount'
        await query.edit_message_text("💬 Введите сумму в гривнах, которую вы хотите перевести:")

    elif query.data == 'subscribe':
        await query.edit_message_text("🔔 Вы подписались на рассылку курса валют (функция пока в разработке).")

    elif query.data == 'unsubscribe':
        await query.edit_message_text("🔕 Вы отписались от рассылки курса валют.")


# Обработка ввода суммы для конвертации
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
            await update.message.reply_text("⚠️ Не удалось получить курс валют.")
            return

        rates = data["rates"]
        usd = round(rates.get("USD", 0) * amount, 2)
        eur = round(rates.get("EUR", 0) * amount, 2)
        pln = round(rates.get("PLN", 0) * amount, 2)
        gbp = round(rates.get("GBP", 0) * amount, 2)
        btc = round(rates.get("BTC", 0) * amount, 6)

        reply = (
            f"💱 Перевод {amount} гривен:\n"
            f"USD: {usd}\n"
            f"EUR: {eur}\n"
            f"PLN: {pln}\n"
            f"GBP: {gbp}\n"
            f"BTC: {btc}"
        )

        await update.message.reply_text(reply)

    except ValueError:
        await update.message.reply_text("❌ Введите сумму в виде числа, например: `1000`", parse_mode='Markdown')

    finally:
        user_states[user_id] = None  # Сброс состояния


# Запуск бота(Пупсика)
def main():
    TELEGRAM_TOKEN = "..."

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))

    print("✅ Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
