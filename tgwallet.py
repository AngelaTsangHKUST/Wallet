import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import os

# Circle API credentials
CIRCLE_API_KEY = os.getenv('CIRCLE_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CIRCLE_BASE_URL = 'https://api.circle.com/v2'


# Setting up basic logging for the application
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function to create a new wallet for a user using the Circle API
def create_circle_wallet(user_id):
    try:
        url = f"{CIRCLE_BASE_URL}/wallets"
        headers = {"Authorization": f"Bearer {CIRCLE_API_KEY}"}
        data = {"idempotencyKey": str(user_id)}
        
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()
        
        if response.ok and "data" in response_data:
            return response_data["data"]
        else:
            logger.error(f"Error creating wallet: Status Code: {response.status_code}, Response: {response_data}")
            return None
    except Exception as e:
        logger.error(f"Exception when creating wallet: {e}")
        return None


# Generic helper function to make API calls
def api_call(url, headers, data):
    try:
        # Sending the request and returning the response
        response = requests.post(url, json=data, headers=headers)
        return response.json()
    except Exception as e:
        logger.error(f"API call error: {e}")
        return None

# Circle API helper function to add a payment method
def add_payment_method(user_id, card_info):
    try:
        url = f"{CIRCLE_BASE_URL}/customers/{user_id}/cards"
        headers = {"Authorization": f"Bearer {CIRCLE_API_KEY}"}
        data = card_info
        response = requests.post(url, json=data, headers=headers)
        return response.json()
    except Exception as e:
        logger.error(f"Error adding payment method: {e}")
        return None

# Command Handlers
async def add_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    card_info = {
        "idempotencyKey": f"add-card-{user_id}",
        "keyId": "your-key-id", 
        "encryptedData": "your-encrypted-card-data", 
        "billingDetails": {
            "name": "Test Name", 
            "city": "Boston",
            "country": "US",
            "line1": "1 Main St",
            "district": "MA",
            "postalCode": "02142"
        },
        "expMonth": 1,
        "expYear": 2023,
        "metadata": {"email": "user@example.com"} 
    }
    
    result = add_payment_method(user_id, card_info)
    if result:
        await update.message.reply_text('Payment method added successfully.')
    else:
        await update.message.reply_text('Error adding payment method. Please try again.')


# Command handler for the 'start' command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    wallet_data = create_circle_wallet(user_id)
    if wallet_data:
        await update.message.reply_text(f'Wallet created with ID: {wallet_data["walletId"]}')
    else:
        await update.message.reply_text('Error creating wallet. Please try again.')

# Command handler for the 'deposit' command
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    result = api_call(f"{CIRCLE_BASE_URL}/wallets/{user_id}/deposits", 
                      {"Authorization": f"Bearer {CIRCLE_API_KEY}"},
                      {"amount": {"amount": 10, "currency": "USD"}, "idempotencyKey": f"deposit-{user_id}-10"})
    if result:
        await update.message.reply_text(f'Deposited 10 units to your wallet. Transaction ID: {result["data"]["transactionId"]}')
    else:
        await update.message.reply_text('Error processing deposit. Please try again.')

# Command handler for the 'withdraw' command
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    result = api_call(f"{CIRCLE_BASE_URL}/wallets/{user_id}/withdrawals", 
                      {"Authorization": f"Bearer {CIRCLE_API_KEY}"},
                      {"amount": {"amount": 5, "currency": "USD"}, "idempotencyKey": f"withdraw-{user_id}-5"})
    if result:
        await update.message.reply_text(f'Withdrew 5 units from your wallet. Transaction ID: {result["data"]["transactionId"]}')
    else:
        await update.message.reply_text('Error processing withdrawal. Please try again.')

# Command handler for the 'transfer' command
async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) == 2 and args[0].isdigit() and args[1].isdigit():
        destination_wallet_id = args[0]
        amount = int(args[1])
        user_id = update.effective_user.id
        result = api_call(f"{CIRCLE_BASE_URL}/transfers", 
                          {"Authorization": f"Bearer {CIRCLE_API_KEY}"},
                          {"source": {"type": "wallet", "id": user_id},
                           "destination": {"type": "wallet", "id": destination_wallet_id},
                           "amount": {"amount": amount, "currency": "USD"},
                           "idempotencyKey": f"transfer-{user_id}-{destination_wallet_id}-{amount}"})
        if result:
            await update.message.reply_text(f'Transferred {amount} units to wallet {destination_wallet_id}. Transaction ID: {result["data"]["transactionId"]}')
        else:
            await update.message.reply_text('Error processing transfer. Please try again.')
    else:
        await update.message.reply_text('Usage: /transfer <destination_wallet_id> <amount>')

# Command handler for echoing back any text messages
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)

# Setting up the Application
if __name__ == '__main__':
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()  
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('deposit', deposit))
    application.add_handler(CommandHandler('withdraw', withdraw))
    application.add_handler(CommandHandler('transfer', transfer))
    application.add_handler(CommandHandler('add_payment', add_payment))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.run_polling()
