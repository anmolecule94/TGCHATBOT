from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pymongo
import google.generativeai as genai
import datetime
import logging
import os
import time
from google.api_core.exceptions import InternalServerError
from dotenv import load_dotenv

google_api_key = os.getenv("GOOGLE_API_KEY")
search_engine_id = os.getenv("SEARCH_ENGINE_ID")
# Load environment variables
dotenv_path = 'C:/Desktop/TGCHATBOT/.env.txt'
load_dotenv(dotenv_path)

# Get MONGO_URI and GEMINI_API_KEY
mongo_uri = os.getenv("MONGO_URI")
gemini_api = os.getenv("GEMINI_API_KEY")

if not mongo_uri:
    raise ValueError("MONGO_URI not found. Check your .env file.")

# MongoDB connection
client = pymongo.MongoClient(mongo_uri)
db = client["chat_bot_db"]
users_collection = db["users"]
chat_history_collection = db["chat_history"]
files_collection = db["files"]

# Configure Gemini AI
genai.configure(api_key=gemini_api)
model = genai.GenerativeModel('gemini-pro')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to handle AI response errors
def safe_generate_content(model, user_input, retries=3, delay=5):
    for _ in range(retries):
        try:
            return model.generate_content(user_input)
        except InternalServerError:
            time.sleep(delay)
    return "Service is currently unavailable. Please try again later."

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command by registering the user and requesting phone number."""
    user = update.message.from_user
    chat_id = update.message.chat_id

    user_data = {
        "first_name": user.first_name,
        "username": user.username,
        "chat_id": chat_id,
        "phone_number": None
    }
    users_collection.update_one({"chat_id": chat_id}, {"$set": user_data}, upsert=True)

    # Request phone number
    contact_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(text="Share Phone Number", request_contact=True)]],
        one_time_keyboard=True
    )
    await update.message.reply_text("Welcome! Please share your phone number:", reply_markup=contact_keyboard)

async def save_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves the user's phone number when shared."""
    phone_number = update.message.contact.phone_number
    chat_id = update.message.chat_id

    users_collection.update_one({"chat_id": chat_id}, {"$set": {"phone_number": phone_number}})
    await update.message.reply_text("Thank you! Your phone number has been saved.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user text messages and responds using Gemini AI."""
    user_input = update.message.text
    chat_id = update.message.chat_id

    response = model.generate_content(user_input)

    # Extract text safely
    bot_reply = response.text if hasattr(response, "text") else "I'm sorry, I couldn't process that."

    await update.message.reply_text(bot_reply)

    # Save chat history
    chat_history = {
        "chat_id": chat_id,
        "user_input": user_input,
        "bot_response": bot_reply,
        "timestamp": datetime.datetime.now()
    }
    chat_history_collection.insert_one(chat_history)


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles image uploads and provides a description using Gemini AI."""
    file = await update.message.photo[-1].get_file()
    file_path = await file.download_to_drive()

    response = safe_generate_content(model, f"Describe this image: {file_path}")
    bot_reply = response if response else "I couldn't analyze this image."

    await update.message.reply_text(bot_reply)

    # Save file metadata
    file_data = {
        "chat_id": update.message.chat_id,
        "filename": file_path,
        "description": bot_reply,
        "timestamp": datetime.datetime.now()
    }
    files_collection.insert_one(file_data)

import re

async def web_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /websearch command by fetching real search results from Google."""
    
    # Get the user's query
    query = " ".join(context.args) if context.args else None

    if not query:
        await update.message.reply_text("Please provide a search query. Example: `/websearch Python programming`")
        return

    # Construct the Google Search API URL
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={google_api_key}&cx={search_engine_id}"

    try:
        response = requests.get(search_url)
        search_results = response.json()

        # Extract top 3 search results
        if "items" in search_results:
            results = search_results["items"][:3]
            reply_text = "\n\n".join([f"🔎 *{item['title']}*\n{item['link']}" for item in results])
        else:
            reply_text = "No results found. Try another query."

        # Escape special Markdown characters
        reply_text = escape_markdown(reply_text)

    except Exception as e:
        reply_text = "An error occurred while searching the web."

    # Send response to Telegram
    await update.message.reply_text(reply_text, parse_mode="Markdown")


def escape_markdown(text):
    """Escapes special characters for Markdown formatting."""
    return re.sub(r'([*_`\[\]()<>)~])', r'\\\1', text)



async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles errors and logs them."""
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    if update:
        await update.message.reply_text("An error occurred. Please try again later.")

if __name__ == "__main__":
    application = Application.builder().token("7600441574:AAGyRqJrK0VdItAU897Toho1XXuOQ2C_LSs").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, save_phone_number))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(CommandHandler("websearch", web_search))
    application.add_error_handler(error_handler)

    # Run bot
    application.add_handler(CommandHandler("start", start))
    application.run_polling()
