import os
import json
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuration
TELEGRAM_BOT_TOKEN = "7669153355:AAHFQrk5U6Uqno-i4v166VRMwdN34fsq8Kk"  # Set your bot token as an environment variable
API_URL = "https://translate-vrv3.onrender.com"  # Replace with your API URL

# Store user levels
user_levels = {}

# Function to escape Markdown V2 special characters
def escape_markdown_v2(text):
    """Escapes special characters for Markdown V2."""
    special_chars = r'_*()~>#+-=|{}.!'
    return ''.join('\\' + char if char in special_chars else char for char in text)

# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message and instructions."""
    welcome_message = escape_markdown_v2("""
🌟 Welcome to the English Learning Bot\! 🌟

Here's how to use me:
1\. Set your level using /set <level> \(e\.g\., /set 25\)\.
2\. Get a Bengali sentence using /get\_ban\.
3\. Translate the sentence and send it back to me for checking\.

Let's get started\! Use /set <level> to begin\.
    """)
    await update.message.reply_text(welcome_message, parse_mode=constants.ParseMode.MARKDOWN_V2)

# Command: Set Level
async def set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the user's level."""
    user_id = update.message.from_user.id
    try:
        level = int(context.args[0])
        if 1 <= level <= 100:
            user_levels[user_id] = level
            await update.message.reply_text(escape_markdown_v2(f"✅ Your level has been set to {level}\. Use /get\_ban to start learning\!"), parse_mode=constants.ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(escape_markdown_v2("❌ Level must be between 1 and 100\."), parse_mode=constants.ParseMode.MARKDOWN_V2)
    except (IndexError, ValueError):
        await update.message.reply_text(escape_markdown_v2("❌ Please provide a valid level\. Usage: /set <level>"), parse_mode=constants.ParseMode.MARKDOWN_V2)

# Command: Get Bengali Sentence
async def get_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get a Bengali sentence for translation."""
    user_id = update.message.from_user.id

    # Check if level is set
    if user_id not in user_levels:
        await update.message.reply_text(escape_markdown_v2("❌ Please set your level first using /set <level>\."), parse_mode=constants.ParseMode.MARKDOWN_V2)
        return

    level = user_levels[user_id]

    # Call the API to get a Bengali sentence
    try:
        response = requests.get(f"{API_URL}/get?level={level}&id={user_id}")
        if response.status_code == 200:
            data = response.json()
            sentence = data.get("sentence")
            tracking_code = data.get("tracking_code")

            # Store the tracking code in the user's context
            context.user_data["tracking_code"] = tracking_code

            await update.message.reply_text(escape_markdown_v2(f"📝 Translate this sentence:\n\n{sentence}"), parse_mode=constants.ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(escape_markdown_v2("❌ Failed to get a sentence\. Please try again later\."), parse_mode=constants.ParseMode.MARKDOWN_V2)
    except Exception as e:
        await update.message.reply_text(escape_markdown_v2(f"❌ An error occurred: {str(e)}"), parse_mode=constants.ParseMode.MARKDOWN_V2)

# Handle Translation Response
async def handle_translation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the user's translation."""
    user_id = update.message.from_user.id
    user_translation = update.message.text

    # Check if there's a tracking code
    tracking_code = context.user_data.get("tracking_code")
    if not tracking_code:
        await update.message.reply_text(escape_markdown_v2("❌ No active translation task\. Use /get\_ban to start\."), parse_mode=constants.ParseMode.MARKDOWN_V2)
        return

    # Call the API to check the translation
    try:
        response = requests.get(f"{API_URL}/translate?code={tracking_code}&en={user_translation}")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "correct":
                message = escape_markdown_v2(
                    f"✅ *Correct\!* 🎉\n\n"
                    f"*Why it's correct:*\n"
                    f"- Your translation matches the Bengali sentence perfectly\.\n"
                    f"- Grammar, spelling, and meaning are all accurate\.\n\n"
                    f"*Correct Translation:* `{data.get('correct_translation')}`"
                )
                await update.message.reply_text(message, parse_mode=constants.ParseMode.MARKDOWN_V2)
            else:
                why_incorrect = escape_markdown_v2(data.get("why", "No specific reason provided."))
                correct_translation = escape_markdown_v2(data.get("correct_translation", "No correct translation provided."))

                error_message = escape_markdown_v2(
                    f"❌ *Incorrect\.* Here's why:\n\n"
                    f"*Why it's incorrect:*\n"
                    f"- {why_incorrect}\n\n"
                    f"*Correct Translation:* `{correct_translation}`"
                )
                await update.message.reply_text(error_message, parse_mode=constants.ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(escape_markdown_v2("❌ Failed to check your translation\. Please try again later\."), parse_mode=constants.ParseMode.MARKDOWN_V2)
    except Exception as e:
        await update.message.reply_text(escape_markdown_v2(f"❌ An error occurred: {str(e)}"), parse_mode=constants.ParseMode.MARKDOWN_V2)

# Main Function
def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_level))
    application.add_handler(CommandHandler("get_ban", get_ban))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_translation))

    # Start the Bot
    print("🚀 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
