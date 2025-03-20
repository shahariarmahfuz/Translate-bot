import os
import requests
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import random

# টেলিগ্রাম বট টোকেন (নিজের টোকেন বসান)
TELEGRAM_BOT_TOKEN = "7669153355:AAHFQrk5U6Uqno-i4v166VRMwdN34fsq8Kk"

# Flask API এর URL (নিজের API লিংক দিন)
TRANSLATE_API_URL = "https://translate-vrv3.onrender.com/translate"

# বাংলা শব্দের তালিকা
 BANGLA_WORDS = [
    " সে বই পড়ে", "গাছ এর নিচে কে?", "আকাশ কত বড় !", "সমুদ্র অনেক সুন্দর", "বন্ধুরা অনেক কাছের", "স্বপ্ন দেখা ভালো", "ভালোবাসা বড় করুন", " সূর্যের আলো অনেক তীব্র", "জল নিয়ে যাই", "মেঘ কি অনেক ঘন?"
 ]

# ইউজারের তথ্য সংরক্ষণ
user_data = {}

def escape_markdown_v2(text):
    """MarkdownV2 ফরম্যাটের জন্য বিশেষ ক্যারেক্টার Escape করা"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def start(update: Update, context: CallbackContext) -> None:
    """ ইউজার যখন /start দিবে, তখন তাকে একটি বাংলা শব্দ দেওয়া হবে """
    user_id = update.message.chat_id
    word = random.choice(BANGLA_WORDS)
    user_data[user_id] = word  # ইউজারের জন্য শব্দ সংরক্ষণ

    await update.message.reply_text(
        f"🔠 *অনুবাদ চ্যালেঞ্জ\!* নিচের বাংলা শব্দটির ইংরেজি লিখুন:\n\n*{escape_markdown_v2(word)}*\n\n✍️ _উত্তর দিন:_",
        parse_mode="MarkdownV2"
    )

async def handle_translation(update: Update, context: CallbackContext) -> None:
    """ ইউজারের উত্তর API-তে পাঠিয়ে যাচাই করা হবে """
    user_id = update.message.chat_id
    user_translation = update.message.text

    if user_id not in user_data:
        await update.message.reply_text("⚠️ অনুগ্রহ করে /start দিয়ে শুরু করুন।", parse_mode="MarkdownV2")
        return

    bangla_word = user_data[user_id]

    # API-তে অনুরোধ পাঠানো
    params = {"ban": bangla_word, "eng": user_translation}
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
            spelling_error = errors.get('spelling', 'বানান ভুল নেই')
            error_text += f"🔠 *Spelling:* _{escape_markdown_v2(spelling_error)}_\n"

            # **Grammar ভুলের তথ্য**
            grammar_error = errors.get('grammar', 'ব্যাকরণ ভুল নেই')
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
        "1️⃣ `/start` দিন, আমরা আপনাকে একটি বাংলা শব্দ দেবো।\n"
        "2️⃣ আপনি এর ইংরেজি অনুবাদ লিখুন।\n"
        "3️⃣ আমরা যাচাই করে বলব সঠিক নাকি ভুল!\n\n"
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
    app.add_handler(CommandHandler("help", help_command))

    # মেসেজ হ্যান্ডলার (ইউজার যে মেসেজ পাঠাবে সেটি হ্যান্ডল করবে)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_translation))

    # বট চালু করুন
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
