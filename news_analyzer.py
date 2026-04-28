#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, requests
from datetime import datetime

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
# Gemini 1.5 Flash with Google Search grounding — free tier
GEMINI_SEARCH_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def ask_gemini_with_search(prompt: str) -> str:
    """Call Gemini with Google Search grounding enabled (free)."""
    if not GEMINI_API_KEY:
        return "⚠️ GEMINI_API_KEY تنظیم نشده."
    try:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],   # Google Search grounding
            "generationConfig": {"maxOutputTokens": 1500, "temperature": 0.7}
        }
        resp = requests.post(
            f"{GEMINI_SEARCH_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=60
        )
        if resp.status_code == 200:
            data = resp.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        # Fallback without search if grounding not available
        payload.pop('tools')
        resp2 = requests.post(f"{GEMINI_SEARCH_URL}?key={GEMINI_API_KEY}", json=payload, timeout=45)
        if resp2.status_code == 200:
            data2 = resp2.json()
            return data2['candidates'][0]['content']['parts'][0]['text']
        return f"❌ خطای Gemini: {resp.status_code}"
    except Exception as e:
        return f"❌ خطای اتصال: {e}"


async def get_local_news_analysis(location: str, period: str = 'daily') -> str:
    period_map = {'daily': 'امروز / ۲۴ ساعت گذشته',
                  'weekly': 'این هفته / ۷ روز گذشته',
                  'monthly': 'این ماه / ۳۰ روز گذشته'}
    period_fa = period_map.get(period, 'امروز')
    today = datetime.now().strftime('%Y/%m/%d')

    prompt = f"""تو یک تحلیلگر اخبار و اقتصاد هستی. به فارسی روان بنویس.

موقعیت کاربر: {location}
تاریخ: {today}
بازه: {period_fa}

با جستجو در اینترنت، آخرین اخبار مهم {location} را بررسی کن و تحلیل زیر را بنویس:

📰 *تحلیل اخبار محلی — {period_fa}*

1. 🔴 مهم‌ترین رویدادهای اخیر در {location}
2. 💹 وضعیت اقتصادی (تورم، قیمت‌ها، بازار)
3. 🏛 رویدادهای سیاسی مؤثر
4. 📈 تأثیر اخبار بر زندگی روزمره مردم
5. ⚠️ هشدارهای مهم (اجتماعی، محیطی، اقتصادی)
6. 💡 توصیه عملی برای ساکنان {location} در این دوره

دقیق، به‌روز و کاربردی باش. از ایموجی استفاده کن."""

    result = ask_gemini_with_search(prompt)
    return f"📰 *اخبار و تحلیل محلی — {period_fa}*\n📍 {location}\n\n━━━━━━━━━━━━━━━━\n\n{result}"
