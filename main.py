import os
import requests
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# টেলিগ্রাম বট টোকেন (নিজের টোকেন বসান)
TELEGRAM_BOT_TOKEN = "7669153355:AAHFQrk5U6Uqno-i4v166VRMwdN34fsq8Kk"

# API URLs
SENTENCE_API_URL = "https://translate-vrv3.onrender.com/get"
TRANSLATE_API_URL = "https://new-ai-buxr.onrender.com/translate"

# ইউজারের তথ্য সংরক্ষণ (লেভেল এবং বর্তমান বাক্য)
user_data = {}

def escape_markdown_v2(text):
    """MarkdownV2 ফরম্যাটের জন্য বিশেষ ক্যারেক্টার Escape করা"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def start(update: Update, context: CallbackContext) -> None:
    """ইউজারকে নতুন বাক্য প্রদান"""
    user_id = update.message.chat_id
    
    # লেভেল চেক করুন
    if user_id not in user_data or 'level' not in user_data[user_id]:
        await update.message.reply_text(
            "⚠️ Please set your level first using:\n\n"
            "Example: `/setlevel 50`\n\n"
            "Level range: 1 to 100",
            parse_mode="MarkdownV2"
        )
        return
    
    # API থেকে বাক্য fetch করুন
    level = user_data[user_id]['level']
    try:
        response = requests.get(SENTENCE_API_URL, params={'level': level})
        response.raise_for_status()
        data = response.json()
        sentence = data.get('sentence', '')
        
        if not sentence:
            raise ValueError("Empty sentence received")
        
        # ইউজার ডেটা আপডেট করুন
        user_data[user_id]['current_sentence'] = sentence
        
        await update.message.reply_text(
            f"🔠 *Translation Challenge\!*\n\nBengali Sentence:\n*{escape_markdown_v2(sentence)}*\n\nTranslate it into English:",
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        await update.message.reply_text("⚠️ Failed to load sentence. Please try again later.")

async def set_level(update: Update, context: CallbackContext) -> None:
    """ইউজারের লেভেল সেট করা"""
    user_id = update.message.chat_id
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "⚠️ Please specify a level. Example:\n"
            "`/setlevel 50`\n\n"
            "Level range: 1 to 100",
            parse_mode="MarkdownV2"
        )
        return
    
    try:
        level = int(args[0])
        if level < 1 or level > 100:
            raise ValueError("Level out of range")
        
        # ইউজার ডেটা আপডেট করুন
        user_data[user_id] = {'level': level}
        
        await update.message.reply_text(
            f"✅ Level set to: *{level}*\n\n"
            "Use `/start` to get a new sentence.",
            parse_mode="MarkdownV2"
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid level! Please choose a number between 1 and 100."
        )

async def handle_translation(update: Update, context: CallbackContext) -> None:
    """ইউজারের উত্তর যাচাই করুন"""
    user_id = update.message.chat_id
    user_translation = update.message.text.strip()

    # ইউজার ডেটা চেক করুন
    if user_id not in user_data or 'current_sentence' not in user_data[user_id]:
        await update.message.reply_text("⚠️ Please use `/start` to begin.", parse_mode="MarkdownV2")
        return

    bangla_sentence = user_data[user_id]['current_sentence']

    # API-তে অনুরোধ পাঠানো
    params = {"ban": bangla_sentence, "eng": user_translation}
    try:
        response = requests.get(TRANSLATE_API_URL, params=params)
        response.raise_for_status()
        result = response.json()

        if result["status"] == "correct":
            reply_text = f"🎉 *Your translation is correct\!*\n\nCorrect translation:\n_{escape_markdown_v2(result['correct_translation'])}_"
        else:
            # ভুল বিশ্লেষণ তৈরি করুন
            errors = []
            if 'spelling' in result['errors']:
                errors.append(f"✍️ Spelling error: {escape_markdown_v2(result['errors']['spelling']}")
            if 'grammar' in result['errors']:
                errors.append(f"📖 Grammar error: {escape_markdown_v2(result['errors']['grammar']}")

            reply_text = (
                f"❌ *Your translation is incorrect\!*\n\n"
                f"{' | '.join(errors)}\n\n"
                f"🔍 Reason: {escape_markdown_v2(result['why']['incorrect_reason'])}\n\n"
                f"✅ Correction: {escape_markdown_v2(result['correct_translation'])}\n\n"
                f"📚 Explanation: {escape_markdown_v2(result['why']['correction_explanation'])}"
            )

        await update.message.reply_text(reply_text, parse_mode="MarkdownV2")
        
        # স্বয়ংক্রিয়ভাবে নতুন বাক্য পাঠানো
        await start(update, context)
        
    except Exception as e:
        await update.message.reply_text("⚠️ Failed to verify translation. Please try again later.")

async def help_command(update: Update, context: CallbackContext) -> None:
    """সহায়তা বার্তা"""
    help_text = (
        "📖 *How to use:*\n\n"
        "1. Set your level first:\n   `/setlevel <level>`\n   (Level range: 1 to 100)\n\n"
        "2. Get a new sentence:\n   `/start`\n\n"
        "3. Type your translation and get AI feedback\n\n"
        "🔄 A new sentence will be sent automatically after each response\n"
        "⚙️ You can change your level anytime"
    )
    await update.message.reply_text(help_text, parse_mode="MarkdownV2")

def main():
    """প্রধান অ্যাপ্লিকেশন"""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # কমান্ড হ্যান্ডলার
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setlevel", set_level))
    app.add_handler(CommandHandler("help", help_command))

    # মেসেজ হ্যান্ডলার
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_translation))

    # বট চালু করুন
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
