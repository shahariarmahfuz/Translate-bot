import os
import requests
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import random

# টেলিগ্রাম বট টোকেন (নিজের টোকেন বসান)
TELEGRAM_BOT_TOKEN = "7669153355:AAHFQrk5U6Uqno-i4v166VRMwdN34fsq8Kk"

# Flask API এর URL (এখানে লেভেল সেটিং এর মাধ্যমে বাংলা সেন্টেন্স পাওয়া যাবে)
TRANSLATE_API_URL = "https://translate-vrv3.onrender.com/get?level={level}"

# ইউজারের তথ্য সংরক্ষণ
user_data = {}

def escape_markdown_v2(text):
    """MarkdownV2 ফরম্যাটের জন্য বিশেষ ক্যারেক্টার Escape করা"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def start(update: Update, context: CallbackContext) -> None:
    """ ইউজার যখন /start দিবে, তখন তাকে লেভেল সেট করতে বলা হবে """
    user_id = update.message.chat_id
    user_data[user_id] = {"level": None}

    await update.message.reply_text(
        "🔠 *Level Setting*\n\nআপনার অনুবাদের জন্য লেভেল সেট করুন।\n"
        "এটি একবার সেট করলে বারবার সেট করতে হবে না।\n\n"
        "লেভেল একটি সংখ্যা হবে ১ থেকে ১০০ পর্যন্ত।\n\n"
        "👉 লেভেল সেট করতে `/setlevel <level>` কমান্ড ব্যবহার করুন। উদাহরণ: `/setlevel 5`",
        parse_mode="MarkdownV2"
    )

async def set_level(update: Update, context: CallbackContext) -> None:
    """ ইউজার লেভেল সেট করবে """
    user_id = update.message.chat_id

    if len(context.args) != 1:
        await update.message.reply_text(
            "⚠️ লেভেল সঠিকভাবে প্রবেশ করুন। উদাহরণ: `/setlevel 5`"
        )
        return

    try:
        level = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ অনুগ্রহ করে একটি বৈধ সংখ্যা প্রবেশ করুন (১ থেকে ১০০)।")
        return

    if level < 1 or level > 100:
        await update.message.reply_text("⚠️ লেভেলটি ১ থেকে ১০০ এর মধ্যে হওয়া উচিত।")
        return

    user_data[user_id]["level"] = level

    await update.message.reply_text(
        f"✔️ আপনার লেভেল সফলভাবে সেট করা হয়েছে: `{escape_markdown_v2(str(level))}`",
        parse_mode="MarkdownV2"
    )

async def fetch_sentence(user_id: str) -> str:
    """ ইউজারের লেভেল অনুযায়ী বাংলা সেন্টেন্স ফেরত পাওয়া """
    level = user_data[user_id]["level"]

    if not level:
        return None

    response = requests.get(TRANSLATE_API_URL.format(level=level))

    if response.status_code == 200:
        data = response.json()
        return data.get("sentence")
    
    return None

async def handle_translation(update: Update, context: CallbackContext) -> None:
    """ ইউজারের অনুবাদ যাচাই করা হবে """
    user_id = update.message.chat_id

    if user_id not in user_data or not user_data[user_id].get("level"):
        await update.message.reply_text(
            "⚠️ আপনার লেভেল এখনও সেট করা হয়নি। `/start` দিয়ে লেভেল সেট করুন।",
            parse_mode="MarkdownV2"
        )
        return

    # API থেকে বাংলা সেন্টেন্স পাওয়া
    bangla_sentence = await fetch_sentence(user_id)

    if not bangla_sentence:
        await update.message.reply_text("⚠️ লেভেল অনুযায়ী সেন্টেন্স পাওয়া যাচ্ছে না। আবার চেষ্টা করুন।", parse_mode="MarkdownV2")
        return

    user_translation = update.message.text

    # Translate API-তে অনুরোধ পাঠানো
    params = {"ban": bangla_sentence, "eng": user_translation}
    response = requests.get("https://new-ai-buxr.onrender.com/translate", params=params)

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
        "1️⃣ `/start` দিন, আমরা আপনাকে একটি লেভেল সেট করতে বলব।\n"
        "2️⃣ আপনি লেভেল সেট করলে, আমরা সেই লেভেলের বাংলা সেন্টেন্স দেবো।\n"
        "3️⃣ আপনি আপনার ইংরেজি অনুবাদ লিখে পাঠাবেন।\n"
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
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setlevel", set_level))

    # মেসেজ হ্যান্ডলার (ইউজার যে মেসেজ পাঠাবে সেটি হ্যান্ডল করবে)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_translation))

    # বট চালু করুন
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
