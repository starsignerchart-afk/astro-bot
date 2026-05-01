#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)
from datetime import datetime

from astrology import calculate_natal_chart, get_daily_chart, get_weekly_chart, get_monthly_chart
from news_analyzer import get_local_news_analysis
from gold_advisor import get_gold_recommendation

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

NAME, BIRTH_DATE, BIRTH_TIME, BIRTH_PLACE, CURRENT_LOCATION, MAIN_MENU = range(6)

# In-memory user storage (Railway ephemeral — good enough for personal/small use)
user_profiles = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🌟 *به ربات طالع‌بینی و مشاور طلا خوش آمدید* 🌟\n\n"
        "این ربات به صورت کاملاً رایگان:\n"
        "✨ چارت تولد دقیق محاسبه می‌کند\n"
        "📊 تحلیل روزانه، هفتگی و ماهیانه می‌دهد\n"
        "📰 اخبار محلی منطقه شما را بررسی می‌کند\n"
        "🥇 پیشنهاد خرید/فروش طلا می‌دهد\n\n"
        "لطفاً *نام* خود را وارد کنید:",
        parse_mode='Markdown'
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ سلام *{context.user_data['name']}* عزیز!\n\n"
        "📅 *تاریخ تولد* خود را وارد کنید:\n"
        "فرمت: روز/ماه/سال میلادی\n"
        "مثال: `15/03/1990`",
        parse_mode='Markdown'
    )
    return BIRTH_DATE


async def get_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        parts = text.replace('-', '/').split('/')
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        context.user_data['birth_date'] = datetime(year, month, day)
        context.user_data['birth_date_str'] = text
    except:
        await update.message.reply_text("❌ فرمت اشتباه! مثال: `15/03/1990`", parse_mode='Markdown')
        return BIRTH_DATE

    await update.message.reply_text(
        "⏰ *ساعت تولد* خود را وارد کنید:\n"
        "فرمت: ساعت:دقیقه — مثال: `14:30`\n"
        "_(اگر نمی‌دانید `12:00` وارد کنید)_",
        parse_mode='Markdown'
    )
    return BIRTH_TIME


async def get_birth_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        h, m = text.split(':')
        context.user_data['birth_hour'] = int(h)
        context.user_data['birth_minute'] = int(m)
        context.user_data['birth_time_str'] = text
    except:
        await update.message.reply_text("❌ فرمت اشتباه! مثال: `14:30`", parse_mode='Markdown')
        return BIRTH_TIME

    await update.message.reply_text(
        "🌍 *محل تولد* خود را وارد کنید:\n"
        "مثال: `تهران، ایران`",
        parse_mode='Markdown'
    )
    return BIRTH_PLACE


async def get_birth_place(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['birth_place'] = update.message.text.strip()
    await update.message.reply_text(
        "📍 *محل سکونت فعلی* خود را وارد کنید:\n"
        "مثال: `تهران، ایران` یا `دبی، امارات`\n"
        "_(برای تحلیل اخبار محلی و نرخ ارز)_",
        parse_mode='Markdown'
    )
    return CURRENT_LOCATION


async def get_current_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    context.user_data['current_location'] = update.message.text.strip()

    user_profiles[user_id] = {
        'name': context.user_data['name'],
        'birth_date': context.user_data['birth_date'],
        'birth_date_str': context.user_data['birth_date_str'],
        'birth_hour': context.user_data.get('birth_hour', 12),
        'birth_minute': context.user_data.get('birth_minute', 0),
        'birth_time_str': context.user_data.get('birth_time_str', '12:00'),
        'birth_place': context.user_data['birth_place'],
        'current_location': context.user_data['current_location'],
    }

    await update.message.reply_text(
        f"✅ *پروفایل ذخیره شد!*\n\n"
        f"👤 {context.user_data['name']}\n"
        f"📅 {context.user_data['birth_date_str']}\n"
        f"⏰ {context.user_data.get('birth_time_str')}\n"
        f"🌍 {context.user_data['birth_place']}\n"
        f"📍 {context.user_data['current_location']}",
        parse_mode='Markdown'
    )
    await show_main_menu(update, context)
    return MAIN_MENU


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 تحلیل روزانه", callback_data='daily'),
         InlineKeyboardButton("📈 تحلیل هفتگی", callback_data='weekly')],
        [InlineKeyboardButton("🗓 تحلیل ماهیانه", callback_data='monthly'),
         InlineKeyboardButton("🥇 مشاور طلا", callback_data='gold')],
        [InlineKeyboardButton("⭐ چارت تولد", callback_data='natal'),
         InlineKeyboardButton("✏️ ویرایش پروفایل", callback_data='edit')],
    ]
    msg = "🌟 *منوی اصلی* — چه تحلیلی می‌خواهید؟"
    if update.message:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == 'edit':
        await query.message.reply_text("✏️ برای ویرایش پروفایل دستور /start را بزنید.")
        return NAME

    if user_id not in user_profiles:
        await query.message.reply_text("⚠️ ابتدا با /start پروفایل بسازید.")
        return MAIN_MENU

    profile = user_profiles[user_id]
    loading_messages = {
        'daily': '⏳ در حال تحلیل روزانه با هوش مصنوعی...',
        'weekly': '⏳ در حال تحلیل هفتگی...',
        'monthly': '⏳ در حال تحلیل ماهیانه...',
        'gold': '⏳ در حال دریافت قیمت طلا و تحلیل...',
        'natal': '⏳ در حال محاسبه چارت تولد...',
    }
    await query.message.reply_text(loading_messages.get(query.data, '⏳ لطفاً صبر کنید...'))

    try:
        if query.data == 'daily':
            result = await get_daily_chart(profile)
        elif query.data == 'weekly':
            result = await get_weekly_chart(profile)
        elif query.data == 'monthly':
            result = await get_monthly_chart(profile)
        elif query.data == 'gold':
            result = await get_gold_recommendation(profile)
        elif query.data == 'natal':
            result = await calculate_natal_chart(profile)
        else:
            result = "❓ گزینه ناشناخته"

        # Telegram max message length = 4096
        if len(result) > 4000:
            chunks = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for chunk in chunks:
                await query.message.reply_text(chunk, parse_mode='Markdown')
        else:
            await query.message.reply_text(result, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

    await show_main_menu(update, context)
    return MAIN_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ لغو شد. برای شروع مجدد /start بزنید.")
    return ConversationHandler.END


def main():
    token = os.environ['TELEGRAM_BOT_TOKEN']
    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birth_date)],
            BIRTH_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birth_time)],
            BIRTH_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birth_place)],
            CURRENT_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_current_location)],
            MAIN_MENU: [CallbackQueryHandler(button_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    logger.info("✅ Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
