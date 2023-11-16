import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Circle API credentials
CIRCLE_API_KEY = '8920b283310dd2883289b84a899d1be3'
CIRCLE_BASE_URL = 'https://api.circle.com/v2'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Circle API helper functions
def create_circle_wallet(user_id):
    url = f"{CIRCLE_BASE_URL}/wallets"
    headers = {"Authorization": f"Bearer {CIRCLE_API_KEY}"}
    data = {"idempotencyKey": str(user_id)}
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def circle_deposit(wallet_id, amount):
    url = f"{CIRCLE_BASE_URL}/wallets/{wallet_id}/deposits"
    headers = {"Authorization": f"Bearer {CIRCLE_API_KEY}"}
    data = {
        "amount": {"amount": amount, "currency": "USD"},
        "idempotencyKey": f"deposit-{wallet_id}-{amount}"
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def circle_withdraw(wallet_id, amount):
    url = f"{CIRCLE_BASE_URL}/wallets/{wallet_id}/withdrawals"
    headers = {"Authorization": f"Bearer {CIRCLE_API_KEY}"}
    data = {
        "amount": {"amount": amount, "currency": "USD"},
        "idempotencyKey": f"withdraw-{wallet_id}-{amount}"
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def circle_transfer(source_wallet_id, destination_wallet_id, amount):
    url = f"{CIRCLE_BASE_URL}/transfers"
    headers = {"Authorization": f"Bearer {CIRCLE_API_KEY}"}
    data = {
        "source": {"type": "wallet", "id": source_wallet_id},
        "destination": {"type": "wallet", "id": destination_wallet_id},
        "amount": {"amount": amount, "currency": "USD"},
        "idempotencyKey": f"transfer-{source_wallet_id}-{destination_wallet_id}-{amount}"
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    wallet = create_circle_wallet(user_id)
    await update.message.reply_text(f'Wallet created with ID: {wallet["data"]["walletId"]}')

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    result = circle_deposit(user_id, 10)  # Example deposit amount
    await update.message.reply_text(f'Deposited 10 units to your wallet. Transaction ID: {result["data"]["transactionId"]}')

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    result = circle_withdraw(user_id, 5)  # Example withdraw amount
    await update.message.reply_text(f'Withdrew 5 units from your wallet. Transaction ID: {result["data"]["transactionId"]}')

async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) == 2 and args[0].isdigit() and args[1].isdigit():
        destination_wallet_id = args[0]
        amount = int(args[1])
        user_id = update.effective_user.id
        result = circle_transfer(user_id, destination_wallet_id, amount)
        await update.message.reply_text(f'Transferred {amount} units to wallet {destination_wallet_id}. Transaction ID: {result["data"]["transactionId"]}')
    else:
        await update.message.reply_text('Usage: /transfer <destination_wallet_id> <amount>')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)

# Setting up the Application
if __name__ == '__main__':
    application = Application.builder().token('6983061584:AAF5m_q_2TrqiPuhd7s1YJTL9NqQh-1pk8o').build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('deposit', deposit))
    application.add_handler(CommandHandler('withdraw', withdraw))
    application.add_handler(CommandHandler('transfer', transfer))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()
