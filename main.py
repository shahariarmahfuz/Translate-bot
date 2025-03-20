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
SENTENCE_API_URL = "https://translate-vrv3.onrender.com/get"

# ইউজারের তথ্য সংরক্ষণ (লেভেল এবং বর্তমান বাক্য)
user_data = {}

def escape_markdown_v2(text):
    """MarkdownV2 ফরম্যাটের জন্য বিশেষ ক্যারেক্টার Escape করা"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def start(update: Update, context: CallbackContext) -> None:
    """ইউজারকে নতুন বাংলা বাক্য প্রদান"""
    user_id = update.message.chat_id
    
    # লেভেল চেক করা
    if user_id not in user_data or 'level' not in user_data[user_id]:
        await update.message.reply_text(
            "⚠️ প্রথমে আপনার লেভেল সেট করুন /setlevel কমান্ড দিয়ে। উদাহরণ: `/setlevel 5`",
            parse_mode="MarkdownV2"
        )
        return
    
    level = user_data[user_id]['level']
    
    # API থেকে বাংলা বাক্য ফেচ করা
    try:
        response = requests.get(f"{SENTENCE_API_URL}?level={level}")
        if response.status_code == 200:
            data = response.json()
            sentence = data.get("sentence", "")
            if not sentence:
                raise ValueError("Empty sentence received")
            
            # ইউজার ডাটা আপডেট
            user_data[user_id]['current_sentence'] = sentence
            
            await update.message.reply_text(
                f"🔠 *অনুবাদ চ্যালেঞ্জ\!* নিচের বাংলা বাক্যটির ইংরেজি লিখুন:\n\n*{escape_markdown_v2(sentence)}*\n\n✍️ _উত্তর দিন:_",
                parse_mode="MarkdownV2"
            )
        else:
            await update.message.reply_text("⚠️ বাক্য লোড করতে সমস্যা হয়েছে। পরে চেষ্টা করুন।")
    
    except Exception as e:
        print(f"API Error: {e}")
        await update.message.reply_text("⚠️ সার্ভার থেকে বাক্য পাওয়া যায়নি। পরে চেষ্টা করুন।")

async def set_level(update: Update, context: CallbackContext) -> None:
    """ইউজারের লেভেল সেট করা"""
    user_id = update.message.chat_id
    args = context.args
    
    if not args or len(args) < 1:
        await update.message.reply_text("⚠️ সঠিক ফরম্যাট: `/setlevel 1-100`", parse_mode="MarkdownV2")
        return
    
    try:
        level = int(args[0])
        if 1 <= level <= 100:
            # ইউজার ডাটা আপডেট
            if user_id not in user_data:
                user_data[user_id] = {}
            user_data[user_id]['level'] = level
            await update.message.reply_text(f"✅ লেভেল সেট করা হয়েছে: {level}\nএখন /start কমান্ড দিয়ে শুরু করুন!")
        else:
            await update.message.reply_text("⚠️ লেভেল ১ থেকে ১০০ এর মধ্যে হতে হবে।")
    
    except ValueError:
        await update.message.reply_text("⚠️ সঠিক সংখ্যা দিন (উদাহরণ: /setlevel 50)")

async def handle_translation(update: Update, context: CallbackContext) -> None:
    """ইউজারের অনুবাদ যাচাই"""
    user_id = update.message.chat_id
    user_translation = update.message.text.strip()

    # বর্তমান বাক্য চেক করা
    if user_id not in user_data or 'current_sentence' not in user_data[user_id]:
        await update.message.reply_text("⚠️ প্রথমে /start কমান্ড দিয়ে শুরু করুন!", parse_mode="MarkdownV2")
        return

    bangla_sentence = user_data[user_id]['current_sentence']

    # অনুবাদ যাচাইয়ের API কল
    params = {"ban": bangla_sentence, "eng": user_translation}
    response = requests.get(TRANSLATE_API_URL, params=params)

    if response.status_code == 200:
        result = response.json()
        
        if result["status"] == "correct":
            reply_text = f"🎉 *সঠিক উত্তর!*\n\n🟢 সঠিক অনুবাদ: _{escape_markdown_v2(result['correct_translation'])}_"
        else:
            # ভুলের বিস্তারিত তথ্য
            errors = result.get("errors", {})
            reason = result.get("why", {})
            correction = result.get("correct_translation", "")
            
            reply_text = "❌ *ভুল উত্তর!*\n\n"
            
            # স্পেলিং ভুল
            if errors.get('spelling'):
                reply_text += f"🔠 *বানান ভুল:* _{escape_markdown_v2(errors['spelling']}_\n"
            
            # গ্রামার ভুল
            if errors.get('grammar'):
                reply_text += f"📖 *ব্যাকরণ ভুল:* _{escape_markdown_v2(errors['grammar']}_\n"
            
            # AI বিশ্লেষণ
            reply_text += f"\n❓ *কারণ:*\n_{escape_markdown_v2(reason.get('incorrect_reason', ''))}_\n"
            reply_text += f"\n🛠 *সংশোধন:*\n_{escape_markdown_v2(reason.get('correction_explanation', ''))}_\n"
            reply_text += f"\n🟢 *সঠিক অনুবাদ:* _{escape_markdown_v2(correction)}_"

        await update.message.reply_text(reply_text, parse_mode="MarkdownV2")
    
    else:
        await update.message.reply_text("⚠️ অনুবাদ যাচাই করতে ব্যর্থ হয়েছে। পরে চেষ্টা করুন।")

async def help_command(update: Update, context: CallbackContext) -> None:
    """হেল্প মেসেজ"""
    help_text = (
        "📚 *বট ব্যবহারের নির্দেশিকা:*\n\n"
        "1\. লেভেল সেট করুন \- `/setlevel <1\-100>` \(যেমন: `/setlevel 20`\)\n"
        "2\. শুরু করুন \- `/start` কমান্ড দিয়ে একটি বাংলা বাক্য পান\n"
        "3\. অনুবাদ জমা দিন \- ইংরেজি অনুবাদ লিখে সেন্ড করুন\n"
        "4\. ফলাফল দেখুন \- AI বিশ্লেষণ সহ উত্তর যাচাই করুন\n\n"
        "🔄 লেভেল পরিবর্তন করতে যেকোনো সময় `/setlevel` ব্যবহার করুন\n"
        "🆘 সাহায্যের জন্য /help লিখুন"
    )
    await update.message.reply_text(help_text, parse_mode="MarkdownV2")

def main():
    """প্রধান ফাংশন"""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # কমান্ড হ্যান্ডলার
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setlevel", set_level))
    app.add_handler(CommandHandler("help", help_command))

    # মেসেজ হ্যান্ডলার
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_translation))

    # বট চালু করুন
    print("🤖 বট সক্রিয়...")
    app.run_polling()

if __name__ == "__main__":
    main()
