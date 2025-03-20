import os
import json
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuration
TELEGRAM_BOT_TOKEN = "7669153355:AAHFQrk5U6Uqno-i4v166VRMwdN34fsq8Kk"  # Set your bot token as an environment variable
API_URL = "https://translate-vrv3.onrender.com"  # Replace with your API URL

# Store user levels
user_levels = {}

# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message and instructions."""
    welcome_message = """
🌟 Welcome to the English Learning Bot! 🌟

Here's how to use me:
1. Set your level using /set <level> (e.g., /set 25).
2. Get a Bengali sentence using /get_ban.
3. Translate the sentence and send it back to me for checking.

Let's get started! Use /set <level> to begin.
    """
    await update.message.reply_text(welcome_message)

# Command: Set Level
async def set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the user's level."""
    user_id = update.message.from_user.id
    try:
        level = int(context.args[0])
        if 1 <= level <= 100:
            user_levels[user_id] = level
            await update.message.reply_text(f"✅ Your level has been set to {level}. Use /get_ban to start learning!")
        else:
            await update.message.reply_text("❌ Level must be between 1 and 100.")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Please provide a valid level. Usage: /set <level>")

# Command: Get Bengali Sentence
async def get_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get a Bengali sentence for translation."""
    user_id = update.message.from_user.id

    # Check if level is set
    if user_id not in user_levels:
        await update.message.reply_text("❌ Please set your level first using /set <level>.")
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

            await update.message.reply_text(f"📝 Translate this sentence:\n\n{sentence}")
        else:
            await update.message.reply_text("❌ Failed to get a sentence. Please try again later.")
    except Exception as e:
        await update.message.reply_text(f"❌ An error occurred: {str(e)}")

# Handle Translation Response
# Handle Translation Response
async def handle_translation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the user's translation."""
    user_id = update.message.from_user.id
    user_translation = update.message.text

    # Check if there's a tracking code
    tracking_code = context.user_data.get("tracking_code")
    if not tracking_code:
        await update.message.reply_text("❌ No active translation task. Use /get_ban to start.")
        return

    # Call the API to check the translation
    try:
        response = requests.get(f"{API_URL}/translate?code={tracking_code}&en={user_translation}")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "correct":
                message = (
                    f"✅ Correct! 🎉\n\n"
                    f"**Why it's correct:**\n"
                    f"- Your translation matches the Bengali sentence perfectly.\n"
                    f"- Grammar, spelling, and meaning are all accurate.\n\n"
                    f"**Correct Translation:** {data.get('correct_translation')}"
                )
                await update.message.reply_text(message)
            else:
                errors = data.get("errors", {})
                why_incorrect = data.get("why", {}).get("incorrect_reason", "No specific reason provided.")
                correction_explanation = data.get("why", {}).get("correction_explanation", "No explanation provided.")

                error_message = (
                    f"❌ Incorrect. Here's why:\n\n"
                    f"**Why it's incorrect:**\n"
                    f"- {why_incorrect}\n\n"
                    f"**Errors:**\n"
                )
                for error_type, error_detail in errors.items():
                    if error_detail:
                        error_message += f"- {error_type}: {error_detail}\n"
                
                error_message += (
                    f"\n**Correction Explanation:**\n"
                    f"- {correction_explanation}\n\n"
                    f"**Correct Translation:** {data.get('correct_translation')}"
                )
                await update.message.reply_text(error_message)
        else:
            await update.message.reply_text("❌ Failed to check your translation. Please try again later.")
    except Exception as e:
        await update.message.reply_text(f"❌ An error occurred: {str(e)}")
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
