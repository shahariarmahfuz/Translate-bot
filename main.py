import os
import requests
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import random

# টেলিগ্রাম বট টোকেন (নিজের টোকেন বসান)
TELEGRAM_BOT_TOKEN = "7669153355:AAHFQrk5U6Uqno-i4v166VRMwdN34fsq8Kk"

# Flask API এর URL (নিজের API লিংক দিন)
TRANSLATE_API_URL = "https://new-ai-buxr.onrender.com/translate"

# API থেকে বাংলা বাক্য পাওয়ার URL
GET_SENTENCE_API_URL = "https://translate-vrv3.onrender.com/get"

# ইউজারের তথ্য সংরক্ষণ (লেভেল এবং টাস্কের জন্য শব্দ/সেন্টেন্স)
user_data = {}

def escape_markdown_v2(text):
    """MarkdownV2 ফরম্যাটের জন্য বিশেষ ক্যারেক্টার Escape করা"""
    escape_chars = r'_*()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def set_level(update: Update, context: CallbackContext) -> None:
    """ ইউজারকে লেভেল সেট করার জন্য হ্যান্ডেল করবে """
    user_id = update.message.chat_id
    try:
        level = int(context.args[0])
        if 1 <= level <= 100:
            user_data[user_id] = {"level": level}
            await update.message.reply_text(f"✅ আপনার লেভেল সেট করা হয়েছে: {level}", parse_mode="MarkdownV2")
        else:
            await update.message.reply_text("⚠️ লেভেল ১ থেকে ১০০ এর মধ্যে হতে হবে।", parse_mode="MarkdownV2")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ লেভেল সেট করার জন্য `/setlevel [১-১০০]` এভাবে লিখুন।", parse_mode="MarkdownV2")

async def start(update: Update, context: CallbackContext) -> None:
    """ ইউজার যখন /start দিবে, তখন তাকে একটি বাংলা বাক্য দেওয়া হবে """
    user_id = update.message.chat_id

    if user_id not in user_data or "level" not in user_data[user_id]:
        await update.message.reply_text("⚙️ অনুগ্রহ করে প্রথমে আপনার লেভেল সেট করুন `/setlevel [১-১০০]` কমান্ড ব্যবহার করে।", parse_mode="MarkdownV2")
        return

    level = user_data[user_id]["level"]
    params = {"level": level}
    try:
        response = requests.get(GET_SENTENCE_API_URL, params=params)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        bangla_sentence = data["sentence"]
        user_data[user_id]["current_sentence"] = bangla_sentence  # ইউজারের জন্য বাক্য সংরক্ষণ

        await update.message.reply_text(
            f"✍️ *অনুবাদ চ্যালেঞ্জ\!* নিচের বাংলা বাক্যটির ইংরেজি লিখুন:\n\n*{escape_markdown_v2(bangla_sentence)}*\n\n📝 _আপনার উত্তর:_ ",
            parse_mode="MarkdownV2"
        )
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"⚠️ বাংলা বাক্য পেতে সমস্যা হচ্ছে: {e}", parse_mode="MarkdownV2")
    except (KeyError, ValueError):
        await update.message.reply_text("⚠️ অপ্রত্যাশিত ত্রুটি ঘটেছে।", parse_mode="MarkdownV2")

async def handle_translation(update: Update, context: CallbackContext) -> None:
    """ ইউজারের উত্তর API-তে পাঠিয়ে যাচাই করা হবে """
    user_id = update.message.chat_id
    user_translation = update.message.text

    if user_id not in user_data or "current_sentence" not in user_data[user_id]:
        await update.message.reply_text("⚠️ অনুগ্রহ করে /start দিয়ে শুরু করুন।", parse_mode="MarkdownV2")
        return

    bangla_sentence = user_data[user_id]["current_sentence"]

    # API-তে অনুরোধ পাঠানো
    params = {"ban": bangla_sentence, "eng": user_translation}
    try:
        response = requests.get(TRANSLATE_API_URL, params=params)
        response.raise_for_status()
        result = response.json()

        if result["status"] == "correct":
            await update.message.reply_text(
                f"✅ *সঠিক অনুবাদ:* _{escape_markdown_v2(result['correct_translation'])}_ 🎉",
                parse_mode="MarkdownV2"
            )
        else:
            errors = result["errors"]
            reason = result["why"]
            correction = result["correct_translation"]

            error_text = "❌ *আপনার উত্তরটি সঠিক নয়\\!*\n\n"

            # **Spelling ভুলের তথ্য**
            spelling_error = errors.get('spelling', '')
            if spelling_error:
                error_text += f"🔠 *বানান:* _{escape_markdown_v2(spelling_error)}_\n"

            # **Grammar ভুলের তথ্য**
            grammar_error = errors.get('grammar', '')
            if grammar_error:
                error_text += f"📖 *ব্যাকরণ:* _{escape_markdown_v2(grammar_error)}_\n"

            # **ভুলের কারণ ও ব্যাখ্যা (AI থেকে সরাসরি)**
            incorrect_reason = escape_markdown_v2(reason.get("incorrect_reason", "ব্যাখ্যা পাওয়া যায়নি"))
            correction_explanation = escape_markdown_v2(reason.get("correction_explanation", "সংশোধনীর ব্যাখ্যা পাওয়া যায়নি"))

            error_text += f"\n❓ *কারণ:* \n> {incorrect_reason}\n"
            error_text += f"\n🛠 *সংশোধনী ব্যাখ্যা:* \n> {correction_explanation}\n"

            # **সঠিক অনুবাদ**
            error_text += f"\n🟢 *সঠিক অনুবাদ:* _{escape_markdown_v2(correction)}_"

            await update.message.reply_text(error_text, parse_mode="MarkdownV2")

    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"⚠️ অনুবাদ যাচাই করতে সমস্যা হচ্ছে: {e}", parse_mode="MarkdownV2")
    except (KeyError, ValueError):
        await update.message.reply_text("⚠️ অপ্রত্যাশিত ত্রুটি ঘটেছে।", parse_mode="MarkdownV2")

async def help_command(update: Update, context: CallbackContext) -> None:
    """ ইউজার যদি /help কমান্ড দেয়, তাহলে নির্দেশনা দেওয়া হবে """
    await update.message.reply_text(
        "📖 *ব্যবহারের নিয়ম:*\n"
        "1️⃣ প্রথমে আপনার লেভেল সেট করুন `/setlevel [১-১০০]` কমান্ড দিয়ে। লেভেল যত কম, বাক্য তত সহজ হবে।\n"
        "2️⃣ `/start` দিন, আমরা আপনাকে একটি বাংলা বাক্য দেবো।\n"
        "3️⃣ আপনি এর ইংরেজি অনুবাদ লিখুন।\n"
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
