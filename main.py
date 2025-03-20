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
            "⚠️ অনুগ্রহ করে প্রথমে আপনার লেভেল সেট করুন:\n\n"
            "উদাহরণ: `/setlevel beginner`\n\n"
            "লেভেল অপশনসমূহ: beginner, intermediate, advanced",
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
            f"🔠 *অনুবাদ চ্যালেঞ্জ\!*\n\nবাংলা বাক্য:\n*{escape_markdown_v2(sentence)}*\n\nইংরেজি অনুবাদ লিখুন:",
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        await update.message.reply_text("⚠️ বাক্য লোড করতে সমস্যা হয়েছে। পরে চেষ্টা করুন।")

async def set_level(update: Update, context: CallbackContext) -> None:
    """ইউজারের লেভেল সেট করা"""
    user_id = update.message.chat_id
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "⚠️ লেভেল নির্দিষ্ট করুন। উদাহরণ:\n"
            "`/setlevel beginner`\n\n"
            "লেভেল অপশনসমূহ:\n- beginner\n- intermediate\n- advanced",
            parse_mode="MarkdownV2"
        )
        return
    
    level = args[0].lower()
    valid_levels = ['beginner', 'intermediate', 'advanced']
    
    if level not in valid_levels:
        await update.message.reply_text(
            "❌ অকার্যকর লেভেল! বৈধ অপশন:\n"
            "- beginner\n- intermediate\n- advanced"
        )
        return
    
    # ইউজার ডেটা আপডেট করুন
    user_data[user_id] = {'level': level}
    
    await update.message.reply_text(
        f"✅ লেভেল সেট করা হয়েছে: *{level}*\n\n"
        "নতুন বাক্য পেতে `/start` কমান্ড ব্যবহার করুন।",
        parse_mode="MarkdownV2"
    )

async def handle_translation(update: Update, context: CallbackContext) -> None:
    """ইউজারের উত্তর যাচাই করুন"""
    user_id = update.message.chat_id
    user_translation = update.message.text.strip()

    # ইউজার ডেটা চেক করুন
    if user_id not in user_data or 'current_sentence' not in user_data[user_id]:
        await update.message.reply_text("⚠️ প্রথমে `/start` কমান্ড দিয়ে শুরু করুন।", parse_mode="MarkdownV2")
        return

    bangla_sentence = user_data[user_id]['current_sentence']

    # API-তে অনুরোধ পাঠানো
    params = {"ban": bangla_sentence, "eng": user_translation}
    try:
        response = requests.get(TRANSLATE_API_URL, params=params)
        response.raise_for_status()
        result = response.json()

        if result["status"] == "correct":
            reply_text = f"🎉 *সঠিক উত্তর!*\n\nসঠিক অনুবাদ:\n_{escape_markdown_v2(result['correct_translation'])}_"
        else:
            # ভুল বিশ্লেষণ তৈরি করুন
            errors = []
            if 'spelling' in result['errors']:
                errors.append(f"✍️ বানান ভুল: {escape_markdown_v2(result['errors']['spelling'])}")
            if 'grammar' in result['errors']:
                errors.append(f"📖 ব্যাকরণ ভুল: {escape_markdown_v2(result['errors']['grammar']}")

            reply_text = (
                f"❌ *ভুল উত্তর*\n\n"
                f"{' | '.join(errors)}\n\n"
                f"🔍 কারণ: {escape_markdown_v2(result['why']['incorrect_reason'])}\n\n"
                f"✅ সংশোধন: {escape_markdown_v2(result['correct_translation'])}\n\n"
                f"📚 ব্যাখ্যা: {escape_markdown_v2(result['why']['correction_explanation'])}"
            )

        await update.message.reply_text(reply_text, parse_mode="MarkdownV2")
        
        # স্বয়ংক্রিয়ভাবে নতুন বাক্য পাঠানো
        await start(update, context)
        
    except Exception as e:
        await update.message.reply_text("⚠️ অনুবাদ যাচাই করতে সমস্যা হচ্ছে। পরে চেষ্টা করুন।")

async def help_command(update: Update, context: CallbackContext) -> None:
    """সহায়তা বার্তা"""
    help_text = (
        "📖 *ব্যবহার নির্দেশিকা:*\n\n"
        "1. প্রথমে লেভেল সেট করুন:\n   `/setlevel <লেভেল>`\n   (লেভেল: beginner/intermediate/advanced)\n\n"
        "2. নতুন বাক্য পেতে:\n   `/start`\n\n"
        "3. আপনার অনুবাদ টাইপ করুন এবং AI ফিডব্যাক পান\n\n"
        "🔄 স্বয়ংক্রিয়ভাবে প্রতিটি উত্তর পরে নতুন বাক্য আসবে\n"
        "⚙️ যেকোনো সময় লেভেল পরিবর্তন করতে পারেন"
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
    print("🤖 বট সক্রিয়...")
    app.run_polling()

if __name__ == "__main__":
    main()
