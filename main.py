import os
import requests
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import random

# টেলিগ্রাম বট টোকেন (নিজের টোকেন বসান)
TELEGRAM_BOT_TOKEN = "7669153355:AAHFQrk5U6Uqno-i4v166VRMwdN34fsq8Kk"

# API URL (নিজের API লিংক দিন)
SENTENCE_API_URL = "https://translate-vrv3.onrender.com/get?level={level}"
TRANSLATE_API_URL = "https://translate-vrv3.onrender.com/translate"

# ইউজারের তথ্য সংরক্ষণ
user_data = {}

def escape_markdown_v2(text):
    """MarkdownV2 ফরম্যাটের জন্য বিশেষ ক্যারেক্টার Escape করা"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def start(update: Update, context: CallbackContext) -> None:
    """ ইউজার যখন /start দিবে, তখন তাকে লেভেল সেট করতে বলা হবে """
    user_id = update.message.chat_id
    await update.message.reply_text(
        "📊 *লেভেল সেট করুন:*\n\n"
        "লেভেল 1 থেকে 100 এর মধ্যে যেকোনো একটি সংখ্যা লিখুন।\n"
        "উদাহরণ: `/setlevel 10`",
        parse_mode="MarkdownV2"
    )

async def set_level(update: Update, context: CallbackContext) -> None:
    """ ইউজার লেভেল সেট করবে """
    user_id = update.message.chat_id
    try:
        level = int(context.args[0])
        if 1 <= level <= 100:
            user_data[user_id] = {"level": level}
            await update.message.reply_text(
                f"✅ লেভেল সেট করা হয়েছে: *{level}*\n\n"
                "এখন আপনি /challenge কমান্ড দিয়ে চ্যালেঞ্জ শুরু করতে পারেন।",
                parse_mode="MarkdownV2"
            )
        else:
            await update.message.reply_text("⚠️ লেভেল 1 থেকে 100 এর মধ্যে হতে হবে।", parse_mode="MarkdownV2")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ সঠিক লেভেল দিন। উদাহরণ: `/setlevel 10`", parse_mode="MarkdownV2")

async def challenge(update: Update, context: CallbackContext) -> None:

async def handle_translation(update: Update, context: CallbackContext) -> None:
    """ ইউজারের উত্তর API-তে পাঠিয়ে যাচাই করা হবে """
    user_id = update.message.chat_id
    user_translation = update.message.text

    if user_id not in user_data or "sentence" not in user_data[user_id]:
        await update.message.reply_text("⚠️ অনুগ্রহ করে /challenge দিয়ে শুরু করুন।", parse_mode="MarkdownV2")
        return

    bangla_sentence = user_data[user_id]["sentence"]

    # API-তে অনুরোধ পাঠানো
    params = {"ban": bangla_sentence, "eng": user_translation}
    response = requests.get(TRANSLATE_API_URL, params=params)

    if response.status_code == 200:
        result = response.json()

        if result["status"] == "correct":
            await update.message.reply_text(
                f"🟢 *Correct translation:* _{escape_markdown_v2(result['correct_translation'])}_",
                parse_mode="MarkdownV2"
            )
        else:
            errors = result["errors"]
            reason = result["why"]
            correction = result["correct_translation"]

            error_text = "❌ *Your sentence is incorrect\\!*\n\n"

            # **Spelling ভুলের তথ্য**
            spelling_error = errors.get('spelling', '')
            if spelling_error:
                error_text += f"🔠 *Spelling:* _{escape_markdown_v2(spelling_error)}_\n"

            # **Grammar ভুলের তথ্য**
            grammar_error = errors.get('grammar', '')
            if grammar_error:
                error_text += f"📖 *Grammar:* _{escape_markdown_v2(grammar_error)}_\n"

            # **ভুলের কারণ ও ব্যাখ্যা (AI থেকে সরাসরি)**
            incorrect_reason = escape_markdown_v2(reason["incorrect_reason"])
            correction_explanation = escape_markdown_v2(reason["correction_explanation"])
            
            error_text += f"\n❓ *Reason:* \n> {incorrect_reason}\n"
            error_text += f"\n🛠 *Correction Explanation:* \n> {correction_explanation}\n"

            # **সঠিক অনুবাদ**
            error_text += f"\n🟢 *Correct translation:* _{escape_markdown_v2(correction)}_"

            await update.message.reply_text(error_text, parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("⚠️ অনুবাদ যাচাই করতে সমস্যা হচ্ছে। পরে চেষ্টা করুন।", parse_mode="MarkdownV2")

async def help_command(update: Update, context: CallbackContext) -> None:
    """ ইউজার যদি /help কমান্ড দেয়, তাহলে নির্দেশনা দেওয়া হবে """
    await update.message.reply_text(
        "📖 *ব্যবহারের নিয়ম:*\n"
        "1️⃣ `/setlevel <লেভেল>` দিয়ে লেভেল সেট করুন (1 থেকে 100)।\n"
        "2️⃣ `/challenge` দিয়ে চ্যালেঞ্জ শুরু করুন।\n"
        "3️⃣ আমরা আপনাকে একটি বাংলা সেন্টেন্স দেবো, আপনি এর ইংরেজি অনুবাদ লিখুন।\n"
        "4️⃣ আমরা যাচাই করে বলব সঠিক নাকি ভুল!\n\n"
        "✅ সঠিক হলে আপনি জিতে যাবেন 🎉\n"
        "❌ ভুল হলে আমরা ভুলটি সংশোধন করে দেখাবো।\n"
        "🚀 শিখুন এবং উন্নতি করুন!",
        parse_mode="MarkdownV2"
    )

def main():
    """ প্রধান ফাংশন যেখানে বট চালানো হবে """
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # কমান্ড হ্যান্ডলার
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setlevel", set_level))
    app.add_handler(CommandHandler("challenge", challenge))
    app.add_handler(CommandHandler("help", help_command))

    # মেসেজ হ্যান্ডলার (ইউজার যে মেসেজ পাঠাবে সেটি হ্যান্ডল করবে)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_translation))

    # বট চালু করুন
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
