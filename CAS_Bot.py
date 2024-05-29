import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue, Job

# Your Telegram bot token
TELEGRAM_BOT_TOKEN = '6371699311:AAE1EkVeUIIQOvK2GM1-zoVmkRLmaF_6bP8'

# Dictionary to store user's target prices
target_prices = {}

# Function to fetch cryptocurrency prices
def get_crypto_price(crypto: str):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies=usd'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if crypto in data:
            return data[crypto]['usd']
        else:
            return None
    except requests.RequestException as e:
        print(f"Error fetching data from CoinGecko: {e}")
        return None

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome to the Crypto Price Bot! Use /price <crypto> to get the price of a cryptocurrency. Use /set_target <crypto> <price> to set a target price.')

# Price command handler
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) > 0:
        crypto = context.args[0].lower()
        price = get_crypto_price(crypto)
        if price is not None:
            await update.message.reply_text(f'The current price of *{crypto}* is *${price:.2f}*', parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text('Invalid cryptocurrency name or data not available.')
    else:
        await update.message.reply_text('Please specify a cryptocurrency. Usage: /price <crypto>')

# Set target command handler
async def set_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text('Usage: /set_target <crypto> <price>')
        return
    
    crypto = context.args[0].lower()
    try:
        target_price = float(context.args[1])
    except ValueError:
        await update.message.reply_text('Invalid price format. Please enter a valid number.')
        return

    user_id = update.message.from_user.id
    target_prices[user_id] = {'crypto': crypto, 'price': target_price}
    await update.message.reply_text(f'Target price for {crypto} set to ${target_price:.2f}')

# Check prices job
async def check_prices(context: ContextTypes.DEFAULT_TYPE):
    for user_id, target in list(target_prices.items()):  # Use list() to avoid runtime dictionary size change errors
        crypto = target['crypto']
        target_price = target['price']
        current_price = get_crypto_price(crypto)
        if current_price and current_price >= target_price:
            await context.bot.send_message(chat_id=user_id, text=f'Target price reached! {crypto} is now ${current_price:.2f}')
            # Remove the user from the target prices dictionary
            del target_prices[user_id]

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        return

    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Get the JobQueue
    job_queue = application.job_queue

    # Register the command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("set_target", set_target))

    # Schedule the job to check prices every minute
    job_queue.run_repeating(check_prices, interval=60, first=10)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
